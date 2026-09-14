import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from processon_harness.secrets import (
    CompositeSecretProvider,
    CredentialError,
    EnvironmentSecretProvider,
    UserConfigSecretProvider,
    default_config_path,
    normalize_token,
)


class TokenNormalizationTest(unittest.TestCase):
    def test_normalizes_raw_and_bearer_tokens(self):
        self.assertEqual("abc-123", normalize_token("abc-123"))
        self.assertEqual("abc-123", normalize_token("  Bearer abc-123  "))
        self.assertEqual("abc-123", normalize_token("bearer   abc-123"))

    def test_rejects_empty_control_characters_and_oversized_values(self):
        invalid = ("", "   ", "line-one\nline-two", "tab\tvalue", "x" * 8193)
        for value in invalid:
            with self.subTest(kind=len(value)):
                with self.assertRaises(CredentialError):
                    normalize_token(value)


class CredentialPathTest(unittest.TestCase):
    def test_explicit_config_path_wins(self):
        expected = Path("/tmp/processon-test-credentials.json")
        actual = default_config_path(
            {
                "PROCESSON_CONFIG_PATH": str(expected),
                "XDG_CONFIG_HOME": "/tmp/ignored-xdg",
            }
        )
        self.assertEqual(expected, actual)

    def test_xdg_config_path_is_used_on_unix(self):
        with mock.patch("os.name", "posix"):
            actual = default_config_path({"XDG_CONFIG_HOME": "/tmp/example-xdg"})
        self.assertEqual(
            Path("/tmp/example-xdg/processon/credentials.json"), actual
        )


class CredentialProviderTest(unittest.TestCase):
    def test_environment_provider_wins_over_saved_credential(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processon" / "credentials.json"
            stored = UserConfigSecretProvider(path)
            stored.save_token("stored-synthetic")
            composite = CompositeSecretProvider(
                [
                    EnvironmentSecretProvider(
                        {"PROCESSON_MCP_TOKEN": "environment-synthetic"}
                    ),
                    stored,
                ]
            )
            self.assertEqual("environment-synthetic", composite.get_token())

    def test_provider_repr_never_contains_a_token(self):
        provider = EnvironmentSecretProvider(
            {"PROCESSON_MCP_TOKEN": "never-print-this-synthetic-token"}
        )
        self.assertNotIn("never-print-this-synthetic-token", repr(provider))

    def test_save_is_normalized_and_reloads_after_cache_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processon" / "credentials.json"
            provider = UserConfigSecretProvider(path)
            provider.save_token("Bearer saved-synthetic")
            self.assertEqual(
                {"PROCESSON_MCP_TOKEN": "saved-synthetic"},
                json.loads(path.read_text(encoding="utf-8")),
            )
            provider.clear_cache()
            self.assertEqual("saved-synthetic", provider.get_token())

    @unittest.skipIf(os.name == "nt", "Unix permission contract")
    def test_save_restricts_directory_and_file_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processon" / "credentials.json"
            provider = UserConfigSecretProvider(path)
            provider.save_token("permission-synthetic")
            self.assertEqual(0o700, stat.S_IMODE(path.parent.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))

    @unittest.skipIf(os.name == "nt", "Unix symlink contract")
    def test_save_rejects_a_symlinked_credential_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            linked = root / "linked"
            linked.symlink_to(real, target_is_directory=True)
            provider = UserConfigSecretProvider(linked / "credentials.json")
            with self.assertRaises(CredentialError):
                provider.save_token("symlink-synthetic")

    def test_failed_atomic_replace_preserves_previous_credential(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processon" / "credentials.json"
            provider = UserConfigSecretProvider(path)
            provider.save_token("first-synthetic")
            with mock.patch("processon_harness.secrets.os.replace", side_effect=OSError):
                with self.assertRaises(CredentialError):
                    provider.save_token("second-synthetic")
            provider.clear_cache()
            self.assertEqual("first-synthetic", provider.get_token())

    def test_malformed_file_is_rejected_without_disclosing_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials.json"
            secret = "malformed-file-synthetic-secret"
            path.write_text(secret, encoding="utf-8")
            provider = UserConfigSecretProvider(path)
            with self.assertRaises(CredentialError) as caught:
                provider.get_token()
            self.assertNotIn(secret, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
