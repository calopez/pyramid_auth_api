"""Define various interfaces telling how user subsystem objects interact and can be looked up from registry."""
# Pyramid
import zope
from pyramid.httpexceptions import HTTPException
from pyramid.interfaces import IResponse
from pyramid.interfaces import IRequest
from zope.interface import Interface

import authomatic

class IUser(Interface):
    """User.
    Hard requirements for User interface listed here
    """

    # : How we present the user's name to the user itself. Usually. Picks one of 1) full name if set
    # 2) username if set 3) email.
    friendly_name = zope.interface.Attribute("friendly_name")


class IGroup(Interface):
    """User group.
    """

    #: Then name of the group
    name = zope.interface.Attribute("name")


class IUserModel(Interface):
    """Register utility registration which marks active User SQLAlchemy model class."""


class IGroupModel(Interface):
    """Register utility registration which marks active Group SQLAlchemy model class."""


class IAuthorizationCode(Interface):
    """Register utility registration which marks Authorization Code SQLAlchemy model class."""

class IActivationModel(Interface):
    """Register utility registration which marks active Activation SQLAlchemy model class."""


class IAuthomatic(Interface):
    """Mark Authomatic instance in the registry."""


class ISocialLoginMapper(Interface):
    """Named marker interface to look up social login mappers."""

    def capture_social_media_user(self, request: IRequest, result: authomatic.core.LoginResult) -> IUserModel:
        """Extract social media information from the Authomatic login result in order to associate the user account."""

    def import_social_media_user(self, user: authomatic.core.User) -> dict:
        """Map incoming social network data to internal data structure.

        Sometimes social networks change how the data is presented over API and you might need to do some wiggling to get it a proper shape you wish to have.

        The resulting dict must be JSON serializable as it is persisted as is.

        :param user: Authomatic user.
        :returns: Dict representation of the user.
        """

    def update_first_login_social_data(self, user: object, data: dict):
        """Set the initial data on the user model.

        When the user logs in from a social network for the first time (no prior logins with this email before) we fill in blanks in the user model with incoming data.

        Default action is not to set any items.

        :param user: User object.
        :param data: Normalized data.
        """


class IFirstLoginManager(Interface):
    """Utility that is responsible to create the initial site."""


class AuthenticationFailure(HTTPException):
    """The user is not allowed to log in."""


class ILoginService(Interface):
    """A service that is responsible for handling normal website facing log in actions.

    This service is responsible to

        * Set up logged in session

        * Do post login actions like redirects
    """

    def authentication_user(user: IUser, login_source: str, location: str=None) -> IResponse:
        """Make the current session logged in session for this particular user.

        A password check is not performed. However it is checked if user is active and such.

        :param login_source: Application specific string telling where the login come from. E.g. "social_media", "signup", "login_form".
        :raise AuthenticationFailure: If the user is disabled
        """

    def authenticate_credentials(username: str, login_source: str, password: str, location: str=None) -> IResponse:
        """Logs in the user.

        This is called after the user credentials have been validated.

        Sets the auth cookies and redirects to a post login page, which defaults to a view named 'index'.

        Fills in user last login time and IP data..

        :param request: Current request

        :param user: Default login service is designed to work with UserMixin compatible user classes

        :param login_source: Application specific string telling where the login come from. E.g. "social_media", "signup", "login_form".

        :raise AuthenticationFailure: If the password does not match or user is disabled
        """

    def logout(location: str=None) -> IResponse:
        """Log out user from the site.

        * Terminate session

        * Show logged out message

        * Redirect the user to post login page
        """


class IOAuthLoginService(Interface):
    """A login service for federated authentication.

    """

    def handle_request(provider_name: str) -> IResponse:
        """Handle all requests coming to login/facebook, login/twitter etc. endpoints.

        * Login form does an empty HTTP POST request to initiate OAuth process

        * Federated authentication service does HTTP GET redirect when they accept OAuth authentication request
        """


class IUserRegistry(Interface):
    """Manage creation and querying of users.

    Allow abstraction over the user backend - do not assume users are stored in the primary database.

    """


class CannotResetPasswordException(HTTPException):
    """Password reset is disabled for this user e.g. due to disabled account."""


class CannotCreateAuthorizationCodeException(HTTPException):
    """Authorization code exchange is disabled for this user e.g. due to disabled account."""


class ICredentialService(Interface):
    """User password and activation related activities. """


class IRegistrationService(Interface):
    """Sign up form service. """


class ILoginSchema(Interface):
    """Colander schema used for sign in form. """


class ILoginForm(Interface):
    """Deform form used for sign in form. """


class IRegisterSchema(Interface):
    """Colander schema used for sign upform. """


class IRegisterForm(Interface):
    """Deform form used for sign upform. """


class IForgotPasswordForm(Interface):
    """Deform form used for Forgot password form. """


class IForgotPasswordSchema(Interface):
    """Colander schema used for Forgot password form. """


class IResetPasswordForm(Interface):
    """Deform form used for Reset password form. """


class IResetPasswordSchema(Interface):
    """Schema used for Reset password form. """


class IPasswordHasher(Interface):
    """A utility for hashing passwords. """

    def hash_password(plain_text: str) -> str:
        """Generate a hash presentation for plain text password.

        This is to be stored in database.

        :return: A hasher internal string format. Usually contains number of cycles, hashed password and salt string.
        """

    def verify_password(hashed_password: str, plain_text: str) -> bool:
        """Verify a password.

        Compare if inputed password matches one stored in the dabase.

        :return: True if the password matches, False otherwise.
        """
