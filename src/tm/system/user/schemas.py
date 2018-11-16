"""Colander schemas."""
# Standard Library
import typing as t

# Pyramid
from pyramid.interfaces import IRequest

from tm.system.user.models import User
from tm.system.user.userregistry import UserRegistry

# Schema validations
from marshmallow import Schema, fields, validate, validates, ValidationError #, EXCLUDE

PASSWORD_MIN_LENGTH = 6


def email_exists(request: IRequest, value: str):
    """Validator that ensures a User exists with the email.

    :param request: Request.
    :param value: Email address.
    :raises: ValidationError if email is not registered for an User.
    """
    exists = request.dbsession.query(User).filter(User.email.ilike(value)).one_or_none()
    if not exists:
        raise ValidationError("Email does not exists: {email}".format(email=value))


class RegisterSchema(Schema):
    """Username-less registration form schema."""

    email = fields.Email()
    password = fields.String(validate=validate.Length(min=PASSWORD_MIN_LENGTH))

    @validates('email')
    def validate_email(self, value):
        dbsession = self.context['request'].dbsession
        value = value.strip()
        if dbsession.query(User).filter_by(email=value).one_or_none():
            raise ValidationError("Email address already taken")

    # class meta:
    #     unknown = EXCLUDE

    # def __call__(self, *args, **kwargs):



class LoginSchema(Schema):
    """Login form schema.

    The user can log in both with email and his/her username, though we recommend using emails as users tend to forget their usernames.
    """
    username = fields.Email(required=True)
    password = fields.String(validate=validate.Length(min=PASSWORD_MIN_LENGTH), required=True)


class ResetPasswordSchema(Schema):
    """Reset password schema."""
    username = fields.String(required=False)
    password = fields.String(validate=validate.Length(min=PASSWORD_MIN_LENGTH), required=True)


class ForgotPasswordSchema(Schema):
    """Used on forgot password view."""
    email = fields.Email()

    @validates('email')
    def validate_email(self, value):
        request = self.context['request']
        user_registry = UserRegistry(request)
        user = user_registry.get_by_email(value)

        if not user:
            raise ValidationError("Cannot reset password for such email: {email}".format(email=value))
