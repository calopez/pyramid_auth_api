"""Register UserEvent subscribers."""
# Pyramid
from pyramid.events import subscriber

# System
from tm.system.user.events import UserCreated
from tm.system.user.models import FirstLoginManager


@subscriber(UserCreated)
def site_init(e: UserCreated):
    """Initialize the website.

    When the first user hits the site, capture its login and add him to the admin group.

    :param e: UserCreated event.
    """
    request = e.request
    user = e.user
    login_manager= FirstLoginManager()
    login_manager.check_first_user_init(request.dbsession, user)
