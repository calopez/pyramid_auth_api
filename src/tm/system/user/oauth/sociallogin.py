# Standard Library
import typing as t

# Pyramid
from pyramid.registry import Registry
from pyramid.request import Request
from zope.interface import implementer

# SQLAlchemy
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

import authomatic

# System
from tm.system.user.events import UserCreated
from tm.system.user.interfaces import ISocialLoginMapper
from tm.system.user.interfaces import IUserModel
from tm.utils.time import now


class NotSatisfiedWithData(Exception):
    """Raised when social media login cannot proceed due to incomplete provided information.

    E.g. we need email to map the user, but the Facebook doesn't give us email because user doesn't grant the permission.
    """


@implementer(ISocialLoginMapper)
class SocialLoginMapper:
    """Base class for mapping internal users to social network (OAuth) users."""

    def __init__(self, registry: Registry, provider_id: str):
        """Create a mapper.

        :param registry: Pyramid configuration used to drive this mapper. Subclasses might want to query this when they create users.
        :param provider_id: String id we use to refer to this authentication source in the configuration file and in the database.
        """
        #: This is the string we use to map configuration for the
        self.provider_id = provider_id
        self.registry = registry

    def activate_user(request, dbsession: Session, user: IUserModel):
        """Checks to perform when the user becomes a valid user for the first time.

        If this user has already started sign up process through email we need to cancel that.
        """
        user.activated_at = now()

        # Cancel any pending email activations if the user chooses the option to use social media login
        if user.activation:
            dbsession.delete(user.activation)

    def update_first_login_social_data(self, user: IUserModel, data: dict):
        """Set the initial data on the user model.

        When the user logs in from a social network for the first time (no prior logins with this email before) we fill in blanks in the user model with incoming data.
        Default action is not to set any items.

        :param user: User object.
        :param data: Normalized data.
        """
        pass

    def update_every_login_social_data(self, user: IUserModel, data: dict):
        """Update internal user data on every login.

        Bt default, sets user.user_data["social"]["facebook"] or user.user_data["social"]["yoursocialnetwork"] to reflect the raw data given us by ``import_social_media_user()``.

        :param user: User object.
        :param data: Normalized data.
        """
        # Non-destructive update - don't remove values which might not be present in the new data
        user.user_data["social"][self.provider_id] = user.user_data["social"].get(self.provider_id) or {}
        user.user_data["social"][self.provider_id].update(data)

        # Because we are doing direct
        flag_modified(user, "user_data")

    def create_blank_user(self, user_model: t.Callable[..., IUserModel], dbsession: Session, email: str) -> IUserModel:
        """Create a new blank user instance as we could not find matching user with the existing details.

        :param user_model: Class to be used for user creation.
        :param dbsession: SQLAlchemy Session object.
        :param email: User email.
        :return: Newly created user.
        """
        user = user_model(email=email)
        dbsession.add(user)
        dbsession.flush()
        user.username = user.generate_username()
        user.registration_source = self.provider_id
        user.activated_at = now()
        return user

    def get_existing_user(self, user_model: t.Callable[..., IUserModel], dbsession: Session, email: str) -> IUserModel:
        """Check if we have a matching user for the email already.

        :param user_model: User class to query for the user with given email.
        :param dbsession: SQLAlchemy Session object.
        :param email: User email.
        :return: User object.
        """
        user = dbsession.query(user_model).filter_by(email=email).first()
        return user

    def get_or_create_user_by_social_medial_email(self, request: Request, user: authomatic.core.User) -> IUserModel:
        """Given a user information returned by Authomatic, return an existing User object from our database or create one if it does not exists.

        :param request: Pyramid request object.
        :param user: A user returned by Authomatic.
        :return: User object.
        """
        User = self.registry.queryUtility(IUserModel)
        dbsession = request.dbsession
        imported_data = self.import_social_media_user(user)
        email = imported_data['email']
        user = self.get_existing_user(User, dbsession, email)
        if not user:
            user = self.create_blank_user(User, dbsession, email)
            request.registry.notify(UserCreated(request, user))
            self.update_first_login_social_data(user, imported_data)
            user.first_login = True
        else:
            user.first_login = False
        self.activate_user(dbsession, user)
        self.update_every_login_social_data(user, imported_data)
        return user