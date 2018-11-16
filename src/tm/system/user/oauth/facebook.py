import authomatic
from authomatic.core import LoginResult
from pyramid.request import Request

from .sociallogin import SocialLoginMapper, NotSatisfiedWithData
from tm.system.user.interfaces import IUserModel


class FacebookMapper(SocialLoginMapper):
    """Map and login Facebook OAuth users to internal users.

    You must have application created in developers.facebook.com

    The application must have its consumer_key and consumer_secret configured in the secrets config file.

    For testing: The application must have one Web site platform configured in developers.facebook.com, pointing to http://localhost:8521/ and Valid OAuth redirect URLs to http://localhost:8521/login/facebook
    """

    def import_social_media_user(self, user: authomatic.core.User) -> dict:
        """Map Authomatic user information to a dictionary.

        :param user: A user returned by Authomatic.
        :return: Mapping from authomatic.core.User.
        """
        return {
            "country": user.country,
            "timezone": user.timezone,
            "gender": user.gender,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.name,
            "link": user.link,
            "birth_date": user.birth_date,
            "city": user.city,
            "postal_code": user.postal_code,
            "email": user.email,
            "id": user.id,
            "nickname": user.nickname,
            # "address": user.address,
        }

    def update_first_login_social_data(self, user: IUserModel, data: dict):
        """Update internal user data on every login.

        :param user: User object.
        :param data: Normalized data.
        """
        super(FacebookMapper, self).update_first_login_social_data(user, data)
        if not user.full_name and data.get("full_name"):
            user.full_name = data["full_name"]

    def capture_social_media_user(self, request: Request, result: LoginResult) -> IUserModel:
        """Extract social media information from the Authomatic login result in order to associate the user account.

        :param request: Pyramid request.
        :param result: Login result from Authomatic.
        :return: User object.
        """
        assert not result.error
        # Facebook specific Authomatic call to fetch more user data from the Facebook provider
        # https://github.com/peterhudec/authomatic/issues/112
        result.user.provider.user_info_url = 'https://graph.facebook.com/me?fields=id,email,name,first_name,last_name,gender,link,timezone,verified'
        result.user.update()

        # Make user Facebook user looks somewhat legit
        assert result.user.credentials
        assert result.user.id

        if not result.user.email:
            # We cannot login if the Facebook doesnt' give us email as we use it for the user mapping
            # This can also happen when you have not configured Facebook app properly in the developers.facebook.com
            raise NotSatisfiedWithData("Email address is needed in order to user this service and we could not get one from your social media provider. Please try to sign up with your email instead.")

        return self.get_or_create_user_by_social_medial_email(request, result.user)





