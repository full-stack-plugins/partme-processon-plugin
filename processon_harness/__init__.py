"""Local runtime support for the cross-host ProcessOn Design plugin."""

from .secrets import (
    CompositeSecretProvider,
    CredentialError,
    EnvironmentSecretProvider,
    UserConfigSecretProvider,
    platform_secret_provider,
)

__all__ = [
    "CompositeSecretProvider",
    "CredentialError",
    "EnvironmentSecretProvider",
    "UserConfigSecretProvider",
    "platform_secret_provider",
]
