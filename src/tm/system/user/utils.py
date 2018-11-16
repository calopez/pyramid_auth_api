"""User utilities."""
# Standard Library
import typing as t

# Pyramid
from pyramid.interfaces import IRequest
from pyramid.registry import Registry

from authomatic import Authomatic

# Websauna
from tm.system.http import Request
from tm.system.user.interfaces import IActivationModel
from tm.system.user.interfaces import IAuthomatic
from tm.system.user.interfaces import ICredentialService
from tm.system.user.interfaces import IGroupModel
from tm.system.user.interfaces import ILoginService
from tm.system.user.interfaces import IOAuthLoginService
from tm.system.user.interfaces import IRegistrationService
from tm.system.user.interfaces import IFirstLoginManager
from tm.system.user.interfaces import ISocialLoginMapper
from tm.system.user.interfaces import IUserModel


def get_user_class(registry: Registry) -> t.Type[IUserModel]:
    """Get the class implementing IUserModel.

    :param registry: Pyramid registry.
    :return: Class implementing IUserModel.
    """
    user_class = registry.queryUtility(IUserModel)
    return user_class


def get_group_class(registry: Registry) -> t.Type[IGroupModel]:
    """Get the class implementing IGroupModel.

    :param registry: Pyramid registry.
    :return: Class implementing IGroupModel.
    """
    group_class = registry.queryUtility(IGroupModel)
    return group_class


def get_activation_model(registry: Registry) -> t.Type[IActivationModel]:
    """Get the class implementing IActivationModel.

    :param registry: Pyramid registry.
    :return: Class implementing IActivationModel.
    """
    activation_model = registry.queryUtility(IActivationModel)
    return activation_model


def get_first_login_manager(registry: Registry) -> IFirstLoginManager:
    """Get the class implementing IFirstLoginManager.

    :param registry: Pyramid registry.
    :return: Class implementing IFirstLoginManager.
    """
    first_login_manager = registry.queryUtility(IFirstLoginManager)
    return first_login_manager


def get_authomatic(registry: Registry) -> Authomatic:
    """Get active Authomatic instance from the registry.

    This is registered in ``Initializer.configure_authomatic()``.
    :param registry: Pyramid registry.
    :return: Instance of Authomatic.
    """
    instance = registry.queryUtility(IAuthomatic)
    return instance


def get_social_login_mapper(registry: Registry, provider_id: str) -> ISocialLoginMapper:
    """Get a named social login mapper.

    Example::

        get_social_login_mapper(registry, "facebook")

    :param registry: Pyramid registry.
    :param provider_id: Provider id of a social login mapper.
    :return: Implementation of ISocialLoginMapper.
    """
    return registry.queryUtility(ISocialLoginMapper, name=provider_id)


def get_login_service(request: Request) -> ILoginService:
    """Get the login service.

    :param request: Pyramid request.
    :return: Implementation of ILoginService.
    """
    assert IRequest.providedBy(request)
    return request.registry.queryAdapter(request, ILoginService)


def get_oauth_login_service(request: Request) -> IOAuthLoginService:
    """Get the oauth login service.

    :param request: Pyramid request.
    :return: Implementation of IOAuthLoginService.
    """
    assert IRequest.providedBy(request)
    return request.registry.queryAdapter(request, IOAuthLoginService)


def get_credential_activity_service(request: Request) -> ICredentialService:
    """Get the credential activity service.

    :param request: Pyramid request.
    :return: Implementation of ICredentialService.
    """
    assert IRequest.providedBy(request)
    return request.registry.queryAdapter(request, ICredentialService)


def get_registration_service(request: Request) -> IRegistrationService:
    """Get the registration service.

    :param request: Pyramid request.
    :return: Implementation of IRegistrationService.
    """
    assert IRequest.providedBy(request)
    return request.registry.queryAdapter(request, IRegistrationService)
