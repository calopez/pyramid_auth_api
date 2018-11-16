from pyramid.security import Allow
from pyramid.security import Everyone


class SampleModel(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, 'group:editors', 'add'),
        (Allow, 'group:editors', 'edit'),
    ]


# if your resources are persistent, an ACL might be specified via -
# the __acl__ attribute of an instance of a resource:

# SampleModel = SampleModel()
#
# SampleModel.__acl__ = [
#         (Allow, Everyone, 'view'),
#         (Allow, 'group:editors', 'add'),
#         (Allow, 'group:editors', 'edit'),
#         ]

# WARNING: For dynamic ACLs, simply use callables:


class Post(object):
    # Special Principal Names: pyramid.security.[Everyone | Authenticated ]
    # Special Permissions: pyramid.security.ALL_PERMISSIONS

    def __acl__(self):
        # Each element of an ACL is an ACE, or access control entry
        return {
            (Allow, Everyone, 'view'),
            (Allow, self.owner, 'edit'),
            # The first element of any ACE is either pyramid.security.Allow, or pyramid.security.Deny, representing the
            # action to take when the ACE matches.
            (Allow,
             'group:editors',  # The second element is a principal i.e  a user or group
             'edit'  # The third argument is a permission or sequence of permission names.
             ),
            # (Allow, 'group:editors', ('add', 'edit')),
        }

    # Special ACEs
    # ------------
    # from pyramid.security import DENY_ALL
    #
    # __acl__ = [ (Allow, 'fred', 'view'), DENY_ALL ]

    # which is equivalent to:

    # from pyramid.security import ALL_PERMISSIONS
    # __acl__ = [ (Deny, Everyone, ALL_PERMISSIONS) ]

    def __init__(self, owner):
        self.owner = owner


# ACL Inheritance and Location-Awareness:
# if a resource object does not have an ACL when it is the context, its parent is consulted for an ACL ad-infinitum

# In order to allow the security machinery to perform ACL inheritance:
# the root object in the resource tree must have a __name__ attribute and a __parent__ attribute.


class RootObject(object):
    __name__ = ''
    __parent__ = None

# Debug View Authorization failures :
# $ PYRAMID_DEBUG_AUTHORIZATION=1 $VENV/bin/pserve myproject.ini
