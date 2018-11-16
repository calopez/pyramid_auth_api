"""Sign up form service."""
# Standard Library
import logging

# Pyramid
from pyramid.httpexceptions import HTTPNoContent
from pyramid.httpexceptions import HTTPNotFound
from pyramid.interfaces import IRequest
from pyramid.response import Response
from pyramid.settings import asbool

from tm.system.user.events import UserCreated
from tm.system.user.events import NewRegistrationEvent
from tm.system.user.events import RegistrationActivatedEvent
from tm.system.mail import send_templated_mail
from tm.system.user.models import User
from system.user.services.login import LoginService
from tm.system.user.userregistry import UserRegistry

logger = logging.getLogger(__name__)


class Message:
    def add(self, *args, **kwargs): pass


messages = Message()


class SignUpService:
    """Default sign up mechanism.

    Send activation email to everybody and ask them to click a link there.
    """

    def __init__(self, request: IRequest):
        """Initialize registration service.

        :param request: Pyramid Request.
        """
        self.request = request
        self.settings = self.request.registry.settings

    def sign_up(self, user_data: dict) -> Response:
        """Sign up a new user.

        :param user_data: User data.
        :return: Either a redirect to a post-signup location or a page informing the user has to activate their account.
        """
        user_registry = UserRegistry(self.request)
        user = user_registry.sign_up(registration_source="email", user_data=user_data)

        # Notify site creator to initialize the admin for the first user
        self.request.registry.notify(UserCreated(self.request, user))

        settings = self.request.registry.settings

        require_activation = asbool(settings.get('tm.registry.require_activation', True))
        autologin = asbool(settings.get('tm.registry.autologin', False))

        if require_activation:
            self.create_email_activation(user)
        elif not autologin:
            messages.add(self.request, msg_id="msg-sign-up-complete", msg="Sign up complete. Welcome!", kind="success")

        self.request.registry.notify(NewRegistrationEvent(self.request, user, None, user_data))
        self.request.dbsession.flush()  # in order to get the id

        if autologin:
            login_service = LoginService(self.request)
            return login_service.authenticate_user(user, login_source="email")
        else:  # not autologin: user must log in just after registering.
            return Response(json_body={'message': "waiting for activation"},  status=200)

    def create_email_activation(self, user: User):
        """Create through-the-web user sign up with his/her email.

        We don't want to force the users to pick up an usernames, so we just generate an username.
        The user is free to change their username later.

        :param user: User object.
        """
        user_registry = UserRegistry(self.request)
        activation_code, expiration_seconds = user_registry.create_email_activation_token(user)
        activation_url_str = self.settings.get('tm.registry.site_user_activation_url')

        context = {
            'link':  '%s/%s' % (activation_url_str, activation_code),
            'expiration_hours': int(expiration_seconds / 3600),
        }

        logger.info("Sending sign up email to %s", user.email)

        # TODO: Broken abstraction, we assume user.email is a attribute
        send_templated_mail(self.request, [user.email], "login/email/activate", context)

    def activate_by_email(self, activation_code: str, location: str = None) -> Response:
        """Active a user after user after the activation email.

            * User clicks link in the activation email
            * User enters the activation code on the form by hand

        :param activation_code: Activation code for user account.
        :param location: URL to redirect the user to, after activation.
        :raise: HTTPNotFound is activation_code is invalid.
        :return: Redirect to location.
        """
        request = self.request
        settings = request.registry.settings
        user_registry = UserRegistry(request)

        login_after_activation = asbool(settings.get('tm.registry.login_after_activation', False))

        user = user_registry.activate_user_by_email_token(activation_code)
        if not user:
            raise HTTPNotFound("Activation code not found")

        if login_after_activation:
            login_service = LoginService(self.request)
            return login_service.authenticate_user(user, login_source="email")
        else:
            self.request.registry.notify(RegistrationActivatedEvent(self.request, user, None))
            return HTTPNoContent(json=None)
