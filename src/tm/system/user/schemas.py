"""Colander schemas."""
# Standard Library
import typing as t

# Pyramid
from pyramid.interfaces import IRequest

from tm.system.user.models import User
from tm.system.user.userregistry import UserRegistry

# Schema validations
# from marshmallow import Schema, fields, validate, validates, ValidationError #, EXCLUDE
import colander as c

PASSWORD_MIN_LENGTH = 6
password = c.SchemaNode(c.String(), validator=c.Length(min=PASSWORD_MIN_LENGTH), required=True)



class SignUpSchema(c.Schema):
    """Username-less registration form schema."""

    def validate_unique_user_email(node: c.SchemaNode, value: str):
        """Make sure we cannot enter the same username twice.

        :param node: Colander SchemaNode.
        :param value: Email address.
        :param kwargs: Keyword arguments.
        :raises: c.Invalid if email address already taken.
        """

        request = node.bindings["request"]
        dbsession = request.dbsession
        value = value.strip()
        if dbsession.query(User).filter_by(email=value).one_or_none():
            raise c.Invalid(node, "Email address already taken")

    email = c.SchemaNode(
        c.String(),
        title='Email',
        validator=c.All(c.Email(), validate_unique_user_email),
    )

    password = password.clone()


class LoginSchema(c.Schema):
    """Login form schema.

    The user can log in both with email and his/her username, though we recommend using emails as users tend to forget their usernames.
    """
    username = c.SchemaNode(c.String(), title='Email', validators=c.Email(), required=True)
    password = password.clone()


class ActivateSchema(c.Schema):
    """Activate schema.

    Activation code is used to activate the account
    """
    code = c.SchemaNode(c.Str(), required=True)

class AuthorizationCodeSchema(c.Schema):
    """AccessToken request schema.

    Authorization code is used to request an access token
    """
    code = c.SchemaNode(c.Str(), required=True)
    client_id = c.SchemaNode(c.Int(), required=True)


class ResetPasswordSchema(c.Schema):
    """Reset password schema."""
    user = c.SchemaNode(c.String(), missing=c.null)
    password = password.clone()


class ForgotPasswordSchema(c.Schema):
    """Used on forgot password request."""

    def validate_user_exist_with_email(node: c.SchemaNode, value: str):
        request = node.bindings['request']
        user_registry = UserRegistry(request)
        user = user_registry.get_by_email(value)
        if not user:
            raise c.Invalid(node, msg='Cannot reset password for such email: {email}'.format(email=value))

    email = c.SchemaNode(
        c.String(),
        validator=c.All(c.Email(), validate_user_exist_with_email),
        description="The email address under which you have your account. Example: joe@example.com"
    )
