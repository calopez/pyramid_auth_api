import authomatic
from authomatic.core import LoginResult
from pyramid.request import Request

from .sociallogin import SocialLoginMapper, NotSatisfiedWithData
from tm.system.user.interfaces import IUserModel


class TwitterMapper(SocialLoginMapper):
    """Map Twitter OAuth users to internal users.

    See :ref:`twitter-auth`.
    """

    @staticmethod
    def _x_user_parser(user: authomatic.core.User, data: dict) -> authomatic.core.User:
        """Monkey patched authomatic.providers.oauth1.Twitter._x_user_parser."""

        # dict_keys(['has_extended_profile', 'profile_use_background_image', 'time_zone', 'profile_image_url', 'default_profile_image', 'lang', 'id', 'id_str', 'profile_sidebar_border_color', 'profile_image_url_https', 'name', 'screen_name', 'utc_offset', 'email', 'location', 'friends_count', 'follow_request_sent', 'contributors_enabled', 'notifications', 'description', 'profile_link_color', 'profile_background_tile', 'followers_count', 'profile_background_image_url_https', 'is_translator', 'is_translation_enabled', 'profile_background_color', 'translator_type', 'profile_text_color', 'created_at', 'geo_enabled', 'profile_sidebar_fill_color', 'verified', 'profile_background_image_url', 'statuses_count', 'following', 'url', 'status', 'entities', 'profile_banner_url', 'default_profile', 'protected', 'favourites_count', 'listed_count'])
        user.data = data
        return user

    def import_social_media_user(self, user: authomatic.core.User):
        """Map Authomatic user information to a dictionary.

        Pass-through Twitter auth data to user_data['social']['twitter']

        :param user: A user returned by Authomatic.
        :return: Mapping from authomatic.core.User.
        """
        return user.data

    def update_first_login_social_data(self, user: IUserModel, data: dict):
        """Set the initial data on the user model.

        :param user: User object.
        :param data: Normalized data.
        """
        super(TwitterMapper, self).update_first_login_social_data(user, data)
        if not user.full_name and data.get("name"):
            user.full_name = data["name"]

    def capture_social_media_user(self, request: Request, result: LoginResult) -> IUserModel:
        """Extract social media information from the Authomatic login result in order to associate the user account.

        :param request: Pyramid request.
        :param result: Login result from Authomatic.
        :return: User object.
        """
        assert not result.error

        # We need to pass include_email=true
        # https://dev.twitter.com/rest/reference/get/account/verify_credentials
        result.provider.user_info_url = "https://api.twitter.com/1.1/account/verify_credentials.json?include_email=true"

        result.user.update()

        # Make user we got some meaningful input from the user_info_url
        assert result.user.credentials

        if not result.user.email:
            # We cannot login if the Facebook doesnt' give us email as we use it for the user mapping
            # This can also happen when you have not configured Facebook app properly in the developers.facebook.com
            raise NotSatisfiedWithData("Email address is needed in order to user this service and we could not get one from your social media provider. Please try to sign up with your email instead.")

        return self.get_or_create_user_by_social_medial_email(request, result.user)