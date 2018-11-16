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
from system.user.oauth.loginservice import OAuthLoginService
from tm.system.user.interfaces import AuthenticationFailure
from tm.system.user.interfaces import CannotResetPasswordException
from tm.system.http import Request
from tm.system.user.schemas import LoginSchema
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
        (Allow, Everyone, 'view'),
        (Allow, 'group:editors', 'add'),
        (Allow, 'group:editors', 'edit'),
    ]


class Message:
    def add(self, *args, **kwargs): pass


messages = Message()

# self.config.add_route('login', '/login', accept='application/json')
# self.config.add_route('logout', '/logout', accept='application/json')
# self.config.add_route('forgot_password', '/forgot-password', accept='application/json')
# self.config.add_route('reset_password', '/reset-password/{code}', accept='application/json')
# self.config.add_route('register', '/register', accept='application/json')
# self.config.add_route('activate', '/activate/{code}', accept='application/json')

# from cornice import Service
# from cornice.validators import marshmallow_body_validator as body_validator

# account = Service(name='account',
#                   path='/account',
#                   description="User account manager")


@view_config(route_name='register', request_method='POST')
# @account.post(schema=RegisterSchema, validators=(body_validator,))
def register(request: Request) -> Response:
    """Sign up view.

    :param request: Pyramid request.
    :return: Pyramid Response
    """
    captured = request.validated
    registration_service = SignUpService(request)
    return registration_service.sign_up(user_data=captured)


@view_config(route_name='login_social')
def login_social(request: Request) -> dict:
    """Login using OAuth and any of the social providers.

    :param request: Pyramid request.
    :return: Context to be used by the renderer.
    """
    # Get the internal provider name URL variable.
    provider_name = request.matchdict.get('provider_name')
    oauth_login_service = OAuthLoginService(request)
    assert oauth_login_service, "OAuth not configured for {}".format(provider_name)
    return oauth_login_service.handle_request(provider_name)


@view_config(route_name='activate', request_method='POST')
def activate(request: Request) -> Response:
    """View to activate user after clicking email link.

    :param request: Pyramid request.
    :return: Context to be used by the renderer.
    """
    code = request.matchdict.get('code', None)
    registration_service = SignUpService(request)
    return registration_service.activate_by_email(code)


@view_config(route_name='login', request_method='POST')
def login(request: Request) -> Response:
    """Default login view implementation.

    :param request: Pyramid request.
    :return: Context to be used by the renderer or a HTTPFound redirect if user is already logged in.
    """
    payload = dict(request.POST.items())
    try:
        captured = LoginSchema().load(payload)
    except ValidationError as e:
        return HTTPUnauthorized(json={'message': e.messages})

    username = captured['username']
    password = captured['password']
    login_service = LoginService(request)

    try:
        return login_service.authenticate_credentials(username, password, login_source="login_form")
    except AuthenticationFailure as e:
        return HTTPUnauthorized(json={'message': str(e)})


@view_config(permission='authenticated', route_name='logout', request_method='POST')
def logout(request: Request) -> Response:
    """Logout view.

    :param request: Pyramid request.
    :return: Context to be used by the renderer.
    """
    # if request.method != "POST":
    #     # No GET / CSRF logouts
    #     return HTTPMethodNotAllowed(json=None)
    login_service = LoginService(request)
    return login_service.logout()


@view_config(route_name='forgot_password', request_method='POST')
def forgot_password(request: Request) -> Response:
    """Forgot password screen.

    :param request: Pyramid request.
    :return: Response
    """
    payload = dict(request.POST.items())
    context = {'request': request}
    try:
        captured = ForgotPasswordSchema(context=context).load(payload)
    except ValidationError as e:
        return HTTPUnprocessableEntity(json={'errors': e.messages})

    credential_activity_service = CredentialService(request)
    email = captured["email"]
    try:
        return credential_activity_service.create_forgot_password_request(email)
    except CannotResetPasswordException as e:
        return HTTPUnprocessableEntity(json={'message': str(e)})


@view_config(route_name='reset_password', request_method='POST')
def reset_password(request: Request) -> Response:
    """Reset password view.

    User arrives on the page and enters the new password.

    :param request: Pyramid request.
    :return: Context to be used by the renderer.
    """
    code = request.matchdict.get('code', None)
    credential_activity_service = CredentialService(request)
    user = credential_activity_service.get_user_for_password_reset_token(code)
    if not user:
        raise HTTPNotFound(json={'message': 'Invalid password reset code'})

    payload = dict(request.POST.items())
    try:
        captured = ResetPasswordSchema().load(payload)
    except ValidationError as e:
        return HTTPUnprocessableEntity(json={'errors': e.messages})

    password = captured['password']
    return credential_activity_service.reset_password(code, password)
