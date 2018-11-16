"""The user authentication helper functions."""
# Pyramid
from pyramid.interfaces import IRequest
# System
import typing as t

from tm.system.user.models import User
from tm.system.user.userregistry import UserRegistry


def get_user(session_token: str, request: IRequest) -> t.Optional[User]:
    """Extract the logged in user from the request object using Pyramid's authentication framework."""
    # user_id = unauthenticated_userid(request)
    # TODO: Abstract this to its own service like in Warehouse?
    user_registry = UserRegistry(request)
    user = None
    if session_token is not None:
        user = user_registry.get_user_by_session_token(session_token)
        # Check through conditions why this user would no longer be valid
        if user and not user.can_login():
            # User account disabled while in mid-session
            user = None
    return user


def get_request_user(request: IRequest) -> t.Optional[User]:
    """Reify method for request.user"""
    user_id = request.unauthenticated_userid
    return get_user(user_id, request) if user_id else None


__all__ = ["get_user", "get_request_user"]
