"""Password reset."""
# Pyramid
from pyramid.httpexceptions import HTTPFound, HTTPCreated, HTTPOk
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from zope.interface import implementer
from pyramid.interfaces import IRequest

# System
from tm.system.user.route import get_config_route
from tm.system.mail import send_templated_mail
from tm.system.user.events import PasswordResetEvent
from tm.system.user.events import UserAuthSensitiveOperation
from tm.system.user.interfaces import CannotResetPasswordException
from tm.system.user.interfaces import ICredentialService
from tm.system.user.interfaces import IUser
from tm.system.user.userregistry import UserRegistry


class Message:
    def add(self, *args, **kwargs): pass


messages = Message()


@implementer(ICredentialService)
class CredentialService:
    """Handle password reset process and such."""

    def __init__(self, request: IRequest):
        self.request = request

    def create_forgot_password_request(self, email: str) -> Response:
        """Create a new email activation token for a user and produce the following screen.

        * Sets user password reset token
        * Sends out reset password email
        * The existing of user with such email should be validated beforehand

        :param email: User email.
        :return: Response.
        :raise: CannotResetPasswordException if there is any reason the password cannot be reset. Usually wrong email.
        """
        request = self.request

        user_registry = UserRegistry(request)

        reset_info = user_registry.create_password_reset_token(email)
        if not reset_info:
            raise CannotResetPasswordException("Cannot reset password for email: {email}".format(email=email))
        user, token, expiration_seconds = reset_info

        link = request.route_path('reset_password', code=token)
        context = dict(link=link, user=user, expiration_hours=int(expiration_seconds / 3600))
        send_templated_mail(request, [email, ], "login/email/forgot_password", context=context)

        return HTTPCreated(json={'message': 'Please check your email to continue password reset.'})

    def get_user_for_password_reset_token(self, activation_code: str) -> IUser:
        """Get a user by activation token.

        :param activation_code: User activation code.
        :return: User for the given activation_code.
        """
        request = self.request
        user_registry = UserRegistry(request)
        user = user_registry.get_user_by_password_reset_token(activation_code)
        return user

    def reset_password(self, activation_code: str, password: str) -> Response:
        """Perform actual password reset operations.

        User has following password reset link (GET) or enters the code on a form.

        :param activation_code: Activation code provided by the user.
        :param password: New user password.
        :return: Response
        :raise: HTTPNotFound if activation_code is not found.
        """
        request = self.request
        user_registry = UserRegistry(request)
        user = user_registry.get_user_by_password_reset_token(activation_code)
        if not user:
            return HTTPNotFound(json={'message': 'Activation code not found'})

        user_registry.reset_password(user, password)

        messages.add(request, msg="The password reset complete. Please sign in with your new password.", kind='success', msg_id="msg-password-reset-complete")

        request.registry.notify(PasswordResetEvent(self.request, user, password))
        request.registry.notify(UserAuthSensitiveOperation(self.request, user, 'password_reset'))

        return HTTPOk(json={'message': "The password reset complete. Please sign in with your new password."})
