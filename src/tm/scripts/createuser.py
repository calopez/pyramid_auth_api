from tm.system.user.models import User
from tm.system.user.models import Group
from tm.utils.time import now

import typing as t


def create(
        dbsession,
        username: str,
        email: str,
        password: t.Optional[str] = None,
        source: str = 'initialize_db_script',
        admin: bool = False
) -> User:
    """Create a new site user from command line.

    :param dbsession:
    :param username: Username, usually an email.
    :param email: User's email.
    :param password: Password.
    :param source: Source of this user, in here, initialize_db_script.
    :param admin: Set this user to admin. The first user is always implicitly admin.
    :return: Newly created user.
    """
    u = dbsession.query(User).filter_by(email=email).first()
    if u is not None:
        return u

    u = User(email=email, username=username)
    dbsession.add(u)
    dbsession.flush()  # Make sure u.user_data is set

    if password:
        # from tm.system.user.userregistry import UserRegistry
        # user_registry = UserRegistry()
        # user_registry.set_password(u, password)
        from tm.system.user.password import Argon2Hasher
        hasher = Argon2Hasher()
        hashed = hasher.hash_password(password)
        u.hashed_password = hashed

    u.registration_source = source
    u.activated_at = now()

    # request.registry.notify(UserCreated(request, u))
    if admin:
        group = dbsession.query(Group).filter_by(name='admin').one_or_none()
        group.users.append(u)

    return u

