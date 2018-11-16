"""Resolve principals (groups and pseudo roles) for ACL."""
# Pyramid
from pyramid.interfaces import IRequest

# Standard Library
import typing as t

def resolve_principals(token: str, request: IRequest) -> t.Optional[t.List[str]]:
    """Get applied groups and other for the user.
    :return: List of principals assigned to the user.
    """
    return request.jwt_claims.get('principals', [])
