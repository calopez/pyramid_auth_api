"""Default login service implementation."""
import logging
# Pyramid
from pyramid.httpexceptions import HTTPOk, HTTPNoContent, HTTPFound
from pyramid.response import Response
from pyramid.security import Authenticated
from pyramid.settings import asbool
from pyramid.settings import aslist

from tm.system.http import Request
from tm.system.user.models import User
from tm.system.user.userregistry import UserRegistry
from tm.utils.time import now

from tm.system.core.utils import get_config_url
from tm.system.user import events
from tm.system.user.interfaces import AuthenticationFailure
from tm.system.user.interfaces import CannotCreateAuthorizationCodeException
import uuid
import sys

logger = logging.getLogger(__name__)

class LoginService:
    """A login service which tries to authenticate with email and username against the current user registry.

    Login service must know details about user implementation and user registry abstraction is not enough.
    """

    def __init__(self, request: Request):
        """Initialize LoginService.

        :param request: Pyramid Request.
        """
        self.request = request

    def update_login_data(self, user: User):
        """Update last_login_at and last_login_ip on User object.

        If this is the User first login, trigger FirstLogin event.

        :param user: User object.
        """
        request = self.request
        if not user.last_login_at:
            e = events.FirstLogin(request, user)
            request.registry.notify(e)

        # Update user security details
        user.last_login_at = now()
        user.last_login_ip = request.client_addr

    def check_credentials(self, username: str, password: str) -> User:
        """Check if the user password matches.

        * First try username + password
        + Then try with email + password

        :param username: username or email
        :param password:
        :raise tm.system.user.interfaces.AuthenticationFailure: On login problem.
        :return: User object which was picked
        """
        request = self.request
        settings = request.registry.settings
        allow_email_auth = settings.get('tm.login.allow_email_auth', True)

        # Check login with username
        user_registry = UserRegistry(request)
        user = user_registry.get_authenticated_user_by_username(username, password)

        # Check login with email
        if allow_email_auth and not user:
            user = user_registry.get_authenticated_user_by_email(username, password)

        if not user:
            raise AuthenticationFailure('Invalid username or password.')

        return user

    def greet_user(self, user: User):
        """Allow easy overriding of a welcome message.

        :param user: User object.
        """
        # messages.add(self.request, kind="success", msg="You are now logged in.", msg_id="msg-you-are-logged-in")

    def do_post_login_actions(self, user: User, headers: dict) -> Response:
        """What happens after a successful login.

        Override this to customize e.g. where the user lands.

        :param user: User object.
        :param headers: Dictionary with headers to be added to the HTTPFound response. i.e Access-Token
        :return: Redirection to location.
        """
        request = self.request

        self.greet_user(user)

        self.update_login_data(user)

        e = events.Login(request, user)
        request.registry.notify(e)

        return HTTPOk(headers=headers, json={})

    def authenticate_user(self, user: User, login_source: str = None) -> Response:
        """Make the current session logged in session for this particular user.

        How to authenticate user using the login service (assuming you have done password match or related yourself):

        .. code-block:: python

            from tm.system.user.loginservice import LoginService

            def my_view(request):

                # load user model instance from database
                # user = ...

                login_service = LoginService(request)
                response = login_service.authenticate_user(user)

        :param user: User object.
        :param login_source: Source of this login.
        :raise AuthenticationFailure: If login cannot proceed due to disabled user account, etc.
        :return: HTTPResponse what should happen as post-login action
        """
        request = self.request
        settings = request.registry.settings

        require_activation = asbool(settings.get('tm.registry.require_activation', True))
        allow_inactive_login = asbool(settings.get('tm.login.allow_inactive_login', False))

        if (not allow_inactive_login) and require_activation and (not user.is_activated()):
            raise AuthenticationFailure('Your account is not active, please check your e-mail. If your account '
                                        'activation email has expired please request a password reset.')

        token = self.__create_jwt_token(user)
        assert token, "Authentication backend did not give us any authentication token"

        return self.do_post_login_actions(user, headers={'Authorization': 'Bearer ' + token})

    def __create_jwt_token(self, user: User) -> str:
        """

        * List all groups as ``group:admin`` style strings
        * List super user as ``superuser:superuser`` style string

        :param user: User object.
        :return: JWT string
        """

        if not user.can_login():
            raise AuthenticationFailure('This user account cannot log in at the moment.')

        principals = [Authenticated]
        principals += ['group:{}'.format(g.name) for g in user.groups]
        principals.append('user:{}'.format(user.id))

        request = self.request
        settings = request.registry.settings
        superusers = aslist(settings.get("tm.login.superusers"))
        admin_as_superuser = asbool(settings.get("tm.login.admin_as_superuser", False))
        # Allow superuser permission
        if user.username in superusers or user.email in superusers:
            # Superuser explicitly listed in the configuration
            principals.append("superuser:superuser")
        elif admin_as_superuser and ("group:admin" in principals):
            # Automatically promote admins to superusers when doing local development
            principals.append("superuser:superuser")

        token = self.request.create_jwt_token(user.id,
                                              name=user.username,
                                              admin=user.is_admin(),
                                              principals=principals)
        return token

    def authenticate_credentials(self, username: str, password: str, login_source: str) -> Response:
        """Try logging in the user with username and password.

        This is called after the user credentials have been validated, after sign up when direct sign in after sign
        up is in use or after successful federated authentication.

        Sets the auth cookies and redirects to a post login page, which defaults to a view named 'index'.

        Fills in user last login time and IP data..

        :param username: Username.
        :param password: User password.
        :param login_source: Source of this login attempt.
        :raise: AuthenticationError
        :return: HTTPResponse what should happen as post-login action
        """
        # See that our user model matches one we expect from the configuration
        user = self.check_credentials(username, password)
        return self.authenticate_user(user, login_source)

    def logout(self) -> Response:
        """Log out user from the site.

        :return: HTTPNoContent empty Authorization header.
        """
        # headers = forget(request)
        headers = {'Authorization': ''}

        return HTTPNoContent(headers=headers, json=None)

    def create_authorization_code(self, user: User, login_source: str) -> Response:
        """Create a new authorization code to be exchanged by an access token

        * Sets authorization code

        :param user: User.
        :return: Response. redirect to the client ui url that knows how to manage the auth code exchange
        :raise: CannotCreateAuthorizationCodeException if there is any reason the authorization code can't be reset.
        """
        user_registry = UserRegistry(self.request)

        auth_code_info = user_registry.create_authorization_code(user)
        if not auth_code_info:
            raise CannotCreateAuthorizationCodeException("Cannot generate authorization code for email: {email}".format(email=user.email))
        user, code, expiration_seconds = auth_code_info

        url = get_config_url(self.request, 'tm.ui_access_token_url')
        authcode_url = "{}?authorizationcode={}&client_id={}&expires_in={}".format(url, code,  user.id, expiration_seconds )
        logger = logging.getLogger('authomatic')
        logger.info("Redirecting user to {}".format( authcode_url))
        return HTTPFound(location=authcode_url)

    def create_access_token(self, client_id, authorization_code):
        """ Exchange authorization code by access token

        :param client_id: the owner of the authorization code
        :param authorization_code: code returned at the end of the social login process i.e facebook, google, etc.
        :return:  HTTPResponse what should happen as post-authenticate_user action
        """
        user_registry = UserRegistry(self.request)
        user = user_registry.validate_authorization_code(client_id, authorization_code)
        if not user:
            raise AuthenticationFailure('Invalid client_id or authorization code.')

        logger = logging.getLogger('authomatic')
        logger.info("User exchange authorization code {} by access token".format(authorization_code))
        return self.authenticate_user(user, login_source='Authorization Code')
