"""Restricted current-user credential storage for ProcessOn."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path


TOKEN_KEY = "PROCESSON_MCP_TOKEN"
CONFIG_PATH_OVERRIDE = "PROCESSON_CONFIG_PATH"
DEFAULT_DIRECTORY_NAME = "processon"
DEFAULT_FILE_NAME = "credentials.json"
MAX_TOKEN_LENGTH = 8192


class CredentialError(RuntimeError):
    """A credential operation failed without exposing credential material."""


def normalize_token(value: str) -> str:
    """Return one validated raw token, accepting an optional Bearer scheme."""
    if not isinstance(value, str):
        raise CredentialError("ProcessOn credential must be text")
    candidate = value.strip()
    parts = candidate.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        candidate = parts[1].strip()
    if not candidate:
        raise CredentialError("ProcessOn credential is empty")
    if len(candidate) > MAX_TOKEN_LENGTH:
        raise CredentialError("ProcessOn credential is too long")
    if any(ord(character) < 32 or ord(character) == 127 for character in candidate):
        raise CredentialError("ProcessOn credential contains invalid characters")
    return candidate


def default_config_path(environ: Mapping[str, str] | None = None) -> Path:
    """Resolve the platform credential path without creating it."""
    values = os.environ if environ is None else environ
    override = values.get(CONFIG_PATH_OVERRIDE, "").strip()
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = values.get("APPDATA", "").strip()
        if not base:
            raise CredentialError("APPDATA is unavailable")
        return Path(base) / DEFAULT_DIRECTORY_NAME / DEFAULT_FILE_NAME
    base = values.get("XDG_CONFIG_HOME", "").strip()
    config_root = Path(base).expanduser() if base else Path.home() / ".config"
    return config_root / DEFAULT_DIRECTORY_NAME / DEFAULT_FILE_NAME


class EnvironmentSecretProvider:
    """Read a raw ProcessOn token from the current process environment."""

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = os.environ if environ is None else environ

    def get_token(self) -> str | None:
        value = self._environ.get(TOKEN_KEY)
        if value is None or not value.strip():
            return None
        return normalize_token(value)

    def clear_cache(self) -> None:
        return None

    def __repr__(self) -> str:
        return "EnvironmentSecretProvider()"


class UserConfigSecretProvider:
    """Read and atomically save a ProcessOn token in current-user state."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = default_config_path() if path is None else Path(path)
        self._cached_token: str | None = None
        self._loaded = False

    def __repr__(self) -> str:
        return f"UserConfigSecretProvider(path={self.path!r})"

    def clear_cache(self) -> None:
        self._cached_token = None
        self._loaded = False

    def get_token(self) -> str | None:
        if self._loaded:
            return self._cached_token
        if not self.path.exists():
            self._loaded = True
            return None
        self._validate_directory(self.path.parent)
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or set(payload) != {TOKEN_KEY}:
                raise ValueError
            token = normalize_token(payload[TOKEN_KEY])
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise CredentialError("ProcessOn credential file is invalid") from exc
        self._cached_token = token
        self._loaded = True
        return token

    def save_token(self, value: str) -> None:
        token = normalize_token(value)
        directory = self.path.parent
        self._prepare_directory(directory)
        temporary_name: str | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.", dir=directory
            )
            if os.name != "nt":
                os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump({TOKEN_KEY: token}, stream, ensure_ascii=False, separators=(",", ":"))
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, self.path)
            temporary_name = None
            if os.name != "nt":
                os.chmod(self.path, 0o600)
                self._fsync_directory(directory)
        except OSError as exc:
            raise CredentialError("Unable to save ProcessOn credential securely") from exc
        finally:
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name)
                except OSError:
                    pass
        self._cached_token = token
        self._loaded = True

    @staticmethod
    def _validate_directory(directory: Path) -> None:
        if directory.is_symlink():
            raise CredentialError("ProcessOn credential directory is not trusted")
        try:
            metadata = directory.stat()
        except OSError as exc:
            raise CredentialError("ProcessOn credential directory is unavailable") from exc
        if os.name != "nt" and hasattr(os, "getuid") and metadata.st_uid != os.getuid():
            raise CredentialError("ProcessOn credential directory has the wrong owner")

    def _prepare_directory(self, directory: Path) -> None:
        if directory.exists() and directory.is_symlink():
            raise CredentialError("ProcessOn credential directory is not trusted")
        try:
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            if os.name != "nt":
                os.chmod(directory, 0o700)
        except OSError as exc:
            raise CredentialError("Unable to prepare ProcessOn credential directory") from exc
        self._validate_directory(directory)

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        try:
            descriptor = os.open(directory, flags)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


class CompositeSecretProvider:
    """Resolve the first available token from an ordered provider list."""

    def __init__(self, providers: Sequence[object]) -> None:
        self.providers = tuple(providers)

    def get_token(self) -> str | None:
        for provider in self.providers:
            token = provider.get_token()
            if token is not None:
                return token
        return None

    def clear_cache(self) -> None:
        for provider in self.providers:
            provider.clear_cache()

    def __repr__(self) -> str:
        return f"CompositeSecretProvider(providers={len(self.providers)})"


def platform_secret_provider() -> CompositeSecretProvider:
    """Build the environment-first ProcessOn credential provider."""
    return CompositeSecretProvider(
        [EnvironmentSecretProvider(), UserConfigSecretProvider()]
    )
