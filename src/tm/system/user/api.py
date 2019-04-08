"""User login and sign up handling views.


.. note ::

    Plan to move something more flexible in the future from these hardcoded, not very feature rich or flexible, views.

"""
# Standard Library
import logging

# Pyramid
from pyramid.httpexceptions import HTTPUnauthorized, HTTPUnprocessableEntity
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.security import Allow, Everyone
from pyramid.view import view_config

# System
from tm.system.user.userregistry import UserRegistry
from tm.system.user.interfaces import AuthenticationFailure
from tm.system.user.interfaces import CannotResetPasswordException
from tm.system.http import Request
from tm.system.user.schemas import LoginSchema, AuthorizationCodeSchema, SignUpSchema, ActivateSchema
from tm.system.user.schemas import ForgotPasswordSchema
from tm.system.user.schemas import ResetPasswordSchema
from tm.system.user.utils import get_oauth_login_service
from tm.system.user.services.login import LoginService
from tm.system.user.services.signup import SignUpService
from tm.system.user.services.credentialactivity import CredentialService

# Schema validations
from marshmallow import ValidationError

logger = logging.getLogger(__name__)


class Blog(object):
    __acl__ = [
        (Allow, Everyone, "view"),
        (Allow, "group:editors", "add"),
        (Allow, "group:editors", "edit"),
    ]


class Message:
    def add(self, *args, **kwargs): pass


messages = Message()

# from cornice.validators import marshmallow_body_validator as body_validator
from cornice import Service
from cornice.validators import colander_body_validator as body_validator
from cornice.validators import colander_querystring_validator as querystring_validator

@view_config(route_name="users", request_method="GET", permission="authenticated")
def users(request: Request) -> Response:
    user_registry = UserRegistry(request)
    result = list(map(lambda u: u.full_name, user_registry.all()))
    return Response(json=result)


account = Service(name="account",
                  path="account/{action}",
                  description="User account manager")
"""
User account manager 
--------------------
To allow the user administer his/her account: create, login, logout, reset password etc.
"""


def signup_schema_validator(request, **kwargs):
    """ SignUpSchema needs request to be in context"""
    kwargs['schema'] = SignUpSchema().bind(request=request)
    return body_validator(request, **kwargs)


@account.post( match_param="action=signup", validators=signup_schema_validator)
def signup(request: Request) -> Response:
    """Sign up view.

    :param request: Pyramid request.
    :return: Pyramid Response
    """
    signup_service = SignUpService(request)
    return signup_service.sign_up(user_data=request.validated)


@account.post(
    match_param="action=activate",
    schema=ActivateSchema(),
    validators=querystring_validator
)
def activate(request: Request) -> Response:
    """View to activate user after clicking email link.

    :param request: Pyramid request.
    :return: Context to be used by the renderer.
    """
    code = request.validated["code"]
    signup_service = SignUpService(request)
    return signup_service.activate_by_email(code)


def forgot_password_schema_validator(request, **kwargs):
    """ SignUpSchema needs request to be in context"""
    kwargs['schema'] = ForgotPasswordSchema().bind(request=request)
    return querystring_validator(request, **kwargs)


@account.post(
    match_param="action=forgot-password",
    schema=ForgotPasswordSchema(),
    validators=forgot_password_schema_validator
)
def forgot_password(request: Request) -> Response:
    """Forgot password email.

    Send an email with a link/code that allows the account change the password
    
    :param request: Pyramid request.
    :return: Response
    """
    credential_activity_service = CredentialService(request)
    email = request.validated["email"]
    try:
        return credential_activity_service.create_forgot_password_request(email)
    except CannotResetPasswordException as e:
        return HTTPUnprocessableEntity(json={"message": str(e)})


@account.post(
    match_param="action=reset-password",
    schema=ResetPasswordSchema(),
    validators=body_validator
)
def reset_password(request: Request) -> Response:
    """Reset password view.

    Given the right token/code it allows reset the account password

    :param request: Pyramid request.
    :return: Context to be used by the renderer.
    """
    code = request.params.get("code", None)
    credential_activity_service = CredentialService(request)
    user = credential_activity_service.get_user_for_password_reset_token(code)
    if not user:
        raise HTTPNotFound(json={"message": "Invalid password reset code"})

    password = request.validated["password"]
    return credential_activity_service.reset_password(code, password)


@account.post(
    match_param="action=logout",
    permission="authenticated"
)
def logout(request: Request) -> Response:
    """Logout view.

    :param request: Pyramid request.
    :return: Context to be used by the renderer.
    """
    login_service = LoginService(request)
    return login_service.logout()


oauth = Service(name="oauth",
                path="/oauth/{action}",
                description="Manage account authentication")

"""
Authorization and authentication stuff
--------------------------------------

"""

@oauth.post(
    match_param="action=token",
    request_param="grant_type=authorization_code",
    schema=AuthorizationCodeSchema(),
    validators=querystring_validator,
)
def token(request: Request) -> Response:
    client_id = request.validated["client_id"]
    authorizationcode = request.validated["code"]
    login_service = LoginService(request)
    return login_service.create_access_token(client_id, authorizationcode)


@oauth.post(
    match_param="action=token",
    request_param="grant_type=password",
    schema=LoginSchema(),
    validators=body_validator
)
def login(request: Request) -> Response:
    """Default login view implementation.

    :param request: Pyramid request.
    :return: Context to be used by the renderer or a HTTPFound redirect if user is already logged in.
    """
    username = request.validated["username"]
    password = request.validated["password"]
    login_service = LoginService(request)

    try:
        return login_service.authenticate_credentials(username, password, login_source="login_form")
    except AuthenticationFailure as e:
        return HTTPUnauthorized(json={"message": str(e)})


authprovider = Service(name="authprovider",
                path="/oauth/login/{provider}",
                description="Manage account authentication through third party providers")

"""
Authorization and authentication through third party providers
--------------------------------------------------------------
    * Facebook
    * Google 
    * Twitter
"""


@authprovider.post()
def social_auth(request: Request) -> Response:
    """Login using OAuth and any of the social providers.

    * Handle the user request for authenticate against one of the auth providers we offer

    :param request: Pyramid request.
    :return: Response
    """
    provider_name = request.matchdict.get("provider_name")
    oauth_login_service = get_oauth_login_service(request)
    assert oauth_login_service, "OAuth not configured for {}".format(provider_name)
    return oauth_login_service.handle_request(provider_name)


@authprovider.get()
def social_auth_redirect(request: Request) -> Response:
    """Login using OAuth and any of the social providers.

    * Handle the redirect from the social auth provider after it  has asked the user for authentication

    :param request: Pyramid request.
    :return: Response
    """
    provider_name = request.matchdict.get("provider_name")
    oauth_login_service = get_oauth_login_service(request)
    assert oauth_login_service, "OAuth not configured for {}".format(provider_name)
    return oauth_login_service.handle_request(provider_name)