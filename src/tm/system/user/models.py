"""Default user model field definitions.

This module defines what fields the default user implementation can have.
"""

# Standard Library
import datetime
from uuid import uuid4

from sqlalchemy.ext.declarative.base import _declarative_constructor
from zope.interface import implementer

# SQLAlchemy
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import inspection
from sqlalchemy.ext.indexable import index_property
from sqlalchemy_utils.types.ip_address import IPAddressType
from sqlalchemy_utils.types.json import JSONType
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy import orm
from sqlalchemy.orm import Session

# System
from tm.system.model.columns import UTCDateTime
# from tm.utils.time import now
from tm.utils.crypt import generate_random_string
from tm.system.user.interfaces import IUserModel, IAuthorizationCode
from tm.system.user.interfaces import IGroupModel
from tm.system.user.interfaces import IActivationModel

now = datetime.datetime.now
#: Initialize user_data JSONB structure with these fields on new User
DEFAULT_USER_DATA = {
    "full_name": None,

    # The initial sign up method (email, phone no, imported, Facebook) for this user
    "registration_source": None,

    # Is it the first time this user is logging to our system? If it is then take the user to fill in the profile page.
    "first_login": True,

    "social": {
        # Each of the social media login data imported here as it goes through
        # SocialLoginMapper.import_social_media_user()
    }
}
# EXAMPLE

# class Example(object):
#     def __acl__(self):
#         return [
#             (Allow, Everyone, 'view'),
#             (Allow, self.owner, ('add', 'edit')),
#             (Allow, self.reviewer, 'review'),
#             (Allow, 'group:editors', 'edit'),
#         ]


@implementer(IUserModel)
class User:
    """A user who signs up with email or with email from social media.

    The user contains normal columns and then ``user_data`` JSON field where properties and non-structured data can \
    be easily added without migrations. This is especially handy to store incoming OAuth fields from social networks. \
    Think Facebook login data and user details.
    """

    # In PSQL "user", the automatically generated table name, is a reserved word
    __tablename__ = "users"

    __init__ = _declarative_constructor

    #: Current user activation instance for reset password for sign up email verification
    activation_id = Column(Integer, ForeignKey("user_activation.id"))

    #: SQLAlchemy relationship for above
    activation = orm.relationship('Activation', backref='user')

    #: Current authorization code instance for exchange access token
    authorization_code_id = Column(Integer, ForeignKey("user_authorization_code.id"))

    #: SQLAlchemy relationship for above
    authorization_code = orm.relationship('AuthorizationCode', backref='user')


    #: Running counter id of the user
    id = Column(Integer, autoincrement=True, primary_key=True)

    #: Publicly exposable ID of the user
    uuid = Column(UUIDType, default=uuid4)

    # : Though not displayed on the site, the concept of "username" is still preserved. If the site needs to have
    # username (think Instagram, Twitter) the user is free to choose this username after the sign up. Username is
    # null until the initial user activation is completed after db.flush() in create_activation().
    username = Column(String(256), nullable=True, unique=True)

    email = Column(String(256), nullable=True, unique=True)

    # : Stores the password + hash + cycles as password hasher internal format.. By default uses Argon 2 format.
    hashed_password = Column('password', String(256), nullable=True)

    #: When this account was created
    created_at = Column(UTCDateTime, default=now)

    #: When the account data was updated last time
    updated_at = Column(UTCDateTime, onupdate=now)

    #: When this user was activated: email confirmed or first social login
    activated_at = Column(UTCDateTime, nullable=True)

    # : Is this user account enabled. The support can lockout/disable the user account in the case of suspected
    # malicious activity.
    enabled = Column(Boolean(name="user_enabled_binary"), default=True)

    # : When this user accessed the system last time. None if the user has never logged in (only activation email
    # sent). Information stored for the security audits.
    last_login_at = Column(UTCDateTime, nullable=True)

    # : From which IP address did this user log in from. If this IP is null the user has never logged in (only
    # activation email sent). Information stored for the security audits. It is also useful for identifying the
    # source country of users e.g. for localized versions.
    last_login_ip = Column(IPAddressType, nullable=True)

    #: Misc. user data as a bag of JSON. Do not access directly, but use JSONBProperties below
    user_data = Column(JSONType, default=DEFAULT_USER_DATA)

    # : Store when this user changed the password or authentication details. Updating this value causes the system to
    #  drop all sessions which were created before this moment. E.g. you will kick out all old sessions on a password
    #  or email change.
    last_auth_sensitive_operation_at = Column(UTCDateTime, nullable=True, default=now)

    #: Full name of the user (if given)
    full_name = index_property("user_data", "full_name")

    # : How this user signed up to the site. May include string like "email", "facebook" or "dummy". Up to the
    # application to use this field. Default social media logins and email sign up set this.
    registration_source = index_property("user_data", "registration_source")

    #: Social media data of the user as a dict keyed by user media
    social = index_property("user_data", "social")

    # : Is this the first login the user manages to do to our system. If this flag is set the user has not logged in
    # to the system before and you can give warm welcoming experience.
    first_login = index_property("user_data", "first_login")

    @property
    def friendly_name(self) -> str:
        """How we present the user's name to the user itself.

        Picks one of 1) full name if set 2) username if set 3) email.
        """
        full_name = self.full_name
        if full_name:
            return full_name

        # Get the username if it looks like non-automatic form
        if self.username:
            if self.username.startswith("user-"):
                return self.email
            else:
                return self.username

        return self.email

    def generate_username(self) -> str:
        """The default username we give for the user."""
        assert self.id
        return "user-{}".format(self.id)

    def is_activated(self) -> bool:
        """Has the user completed the email activation."""
        return self.activated_at is not None

    def can_login(self) -> bool:
        """Is this user allowed to login."""
        # TODO: is_active defined in Horus
        return self.enabled and self.is_activated()

    def is_in_group(self, name) -> bool:

        # TODO: groups - defined in Horus
        for g in self.groups:
            if g.name == name:
                return True
        return False

    def is_admin(self) -> bool:
        """Does this user the see the main admin interface link.

        TODO: This is very suboptimal, wasted database cycles, etc. Change this.
        """
        return self.is_in_group(Group.DEFAULT_ADMIN_GROUP_NAME)

    def is_valid_session(self, session_created_at: datetime.datetime) -> bool:
        """Check if the current session is still valid for this user."""
        return self.last_auth_sensitive_operation_at <= session_created_at

    def __str__(self):
        return self.friendly_name

    def __repr__(self):
        return "#{}: {}".format(self.id, self.friendly_name)


@implementer(IGroupModel)
class Group:
    #: Assign the first user initially to this group
    DEFAULT_ADMIN_GROUP_NAME = "admin"

    __tablename__ = "group"

    __init__ = _declarative_constructor

    users = orm.relationship(
        'User',
        secondary='usergroup',
        passive_deletes=True,
        passive_updates=True,
        backref="groups",
    )

    def __repr__(self):
        """Representation of a Group object."""
        return "Group #{id}: {name}".format(id=self.id, name=self.name)

    #: Running counter id of the group
    id = Column(Integer, autoincrement=True, primary_key=True)

    #: Public ID of the group
    uuid = Column(UUIDType, default=uuid4)

    #: Human readable / machine referrable name of the group
    name = Column(String(64), unique=True)

    #: Human readable description of the group
    description = Column(String(256))

    #: When this group was created.
    created_at = Column(UTCDateTime, default=now)

    # : When the group was updated last time. Please note that this does not concern group membership,
    # only description updates.
    updated_at = Column(UTCDateTime, onupdate=now)

    #: Extra JSON data to be stored with this group
    group_data = Column(JSONType, default=dict)



@implementer(IAuthorizationCode)
class AuthorizationCode:
    """Authorization code to be exchanged for an access token

    user authorization code
    """

    __tablename__ = "user_authorization_code"

    __init__ = _declarative_constructor

    #: Running counter id
    id = Column(Integer, autoincrement=True, primary_key=True)
    created_at = Column(UTCDateTime, default=now)
    updated_at = Column(UTCDateTime, onupdate=now)

    #: All authorization code must have expiring time
    expires_at = Column(UTCDateTime, nullable=False)

    code = Column(String(32), nullable=False, unique=True, default=lambda: generate_random_string(32))

    def is_expired(self):
        """The activation best before is past and we should not use it anymore."""
        return self.expires_at < now()


@implementer(IActivationModel)
class Activation:
    """Sign up / forgot password activation code reference.

    user email activation token
    """

    __tablename__ = "user_activation"

    __init__ = _declarative_constructor

    #: Running counter id
    id = Column(Integer, autoincrement=True, primary_key=True)
    created_at = Column(UTCDateTime, default=now)
    updated_at = Column(UTCDateTime, onupdate=now)

    #: All activation tokens must have expiring time
    expires_at = Column(UTCDateTime, nullable=False)

    code = Column(String(32), nullable=False, unique=True, default=lambda: generate_random_string(32))

    def is_expired(self):
        """The activation best before is past and we should not use it anymore."""
        return self.expires_at < now()


class UserGroup:
    """Map one user to one group."""

    __tablename__ = "usergroup"

    __init__ = _declarative_constructor

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(ForeignKey("users.id"))
    group_id = Column(ForeignKey("group.id"))


# from sqlalchemy import inspect
#
# def object_as_dict(obj):
#     return {c.key: getattr(obj, c.key)
#             for c in inspect(obj).mapper.column_attrs}
#
# user = session.query(User).first()
#
# d = object_as_dict(user)
#
# method can be used if you’re querying a specific field because it is returned as a KeyedTuple.
# In [1]: foo = db.session.query(Topic.name).first()
# In [2]: foo._asdict()
# Out[2]: {'name': u'blah'}


class FirstLoginManager:
    """Component responsible for setting up an empty site on first login.

    The site creator is run by the activation of the first user. This either happens¨

    * When the activation email is sent to the first user

    * When the first user logs through social media account

    """

    def init_first_user(self, dbsession: Session, user: User):
        """When the first user signs up build the admin groups and make the user member of it.

        Make the first member of the site to be admin and superuser.
        """
        # Try to reflect related group class based on User model
        i = inspection.inspect(user.__class__)
        Group = i.relationships["groups"].mapper.entity

        # Do we already have any groups... if we do we probably don'¨t want to init again
        if dbsession.query(Group).count() > 0:
            return
        g = Group(name=Group.DEFAULT_ADMIN_GROUP_NAME)
        dbsession.add(g)
        g.users.append(user)

    def check_first_user_init(self, dbsession: Session, user: User):
        """Call after user creation to see if this user is the first user and should get initial admin rights."""
        assert user.id, "Please flush your db"

        # Try to reflect related group class based on User model
        i = inspection.inspect(user.__class__)
        Group = i.relationships["groups"].mapper.entity

        # If we already have groups admin group must be there
        if dbsession.query(Group).count() > 0:
            return

        self.init_first_user(dbsession, user)


__all__ = ["User", "Group", "Activation", "FirstLoginManager", "AuthorizationCode"]
