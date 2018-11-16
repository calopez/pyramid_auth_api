import authomatic
from authomatic.core import LoginResult
from pyramid.request import Request

from .sociallogin import SocialLoginMapper, NotSatisfiedWithData
from tm.system.user.interfaces import IUserModel


class GoogleMapper(SocialLoginMapper):
    """Map and login Google OAuth users to internal users.

    See :ref:`google-auth`.
    """

    def import_social_media_user(self, user: authomatic.core.User):
        """Map Authomatic user information to a dictionary.

        ref: http://peterhudec.github.io/authomatic/reference/providers.html#authomatic.providers.oauth2.Google

        :param user: A user returned by Authomatic.
        :return: Mapping from authomatic.core.User.
        """
        return {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.name,
            "locale": user.locale,
            "picture": user.picture,
            "email_verified": user.email_verified,
        }

    def update_first_login_social_data(self, user: IUserModel, data: dict):
        """Set the initial data on the user model.

        :param user: User object.
        :param data: Normalized data.
        """
        super(GoogleMapper, self).update_first_login_social_data(user, data)
        if not user.full_name and data.get("full_name"):
            user.full_name = data["full_name"]

    def capture_social_media_user(self, request: Request, result: LoginResult) -> IUserModel:
        """Extract social media information from the Authomatic login result in order to associate the user account.

        :param request: Pyramid request.
        :param result: Login result from Authomatic.
        :return: User object.
        """
        assert not result.error

        result.user.update()
        # Make user we got some meaningful input from the user_info_url
        assert result.user.credentials

        if not result.user.email_verified:
            raise NotSatisfiedWithData("User account email is not verified.")

        if not result.user.email:
            # We cannot login if the Facebook doesnt' give us email as we use it for the user mapping
            # This can also happen when you have not configured Facebook app properly in the developers.facebook.com
            raise NotSatisfiedWithData("Email address is needed in order to user this service and we could not get one from your social media provider. Please try to sign up with your email instead.")

        return self.get_or_create_user_by_social_medial_email(request, result.user)