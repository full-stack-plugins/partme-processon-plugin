import contextlib
import io
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from processon_harness.secrets import UserConfigSecretProvider
from scripts.processon_setup import (
    build_parser,
    create_setup_server,
    credential_status,
    run_hidden_setup,
)


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "setup"


class SetupPageTest(unittest.TestCase):
    def test_page_has_one_three_step_password_flow(self):
        html = (ASSETS / "index.html").read_text(encoding="utf-8")
        self.assertEqual(1, html.count('class="setup-card"'))
        self.assertEqual(3, html.count('class="setup-step"'))
        self.assertIn('class="brand-lockup"', html)
        self.assertIn('href="https://smart.processon.com/user"', html)
        self.assertEqual(1, html.count('type="password"'))
        self.assertIn('id="launch"', html)
        self.assertIn("<details", html)
        self.assertNotIn('value="', html)

    def test_page_uses_local_assets_and_clears_input_after_save(self):
        html = (ASSETS / "index.html").read_text(encoding="utf-8")
        script = (ASSETS / "app.js").read_text(encoding="utf-8")
        self.assertIn('href="/styles.css"', html)
        self.assertIn('src="/app.js"', html)
        self.assertNotIn("https://fonts", html)
        self.assertIn("finally", script)
        self.assertIn('tokenInput.value = ""', script)
        self.assertIn("launchButton.disabled = false", script)

    def test_page_matches_the_approved_stitch_setup_visual_system(self):
        css = (ASSETS / "styles.css").read_text(encoding="utf-8")
        self.assertIn("--processon-blue: #2f80ed", css.lower())
        self.assertIn("radial-gradient(circle at 38% 48%", css)
        self.assertIn("radial-gradient(circle at 66% 45%", css)
        self.assertIn("border-radius: 28px", css)
        self.assertNotIn(".blueprint-grid", css)
        self.assertNotIn(".flow-line", css)


class SetupCliTest(unittest.TestCase):
    def test_parser_accepts_all_setup_commands(self):
        parser = build_parser()
        for arguments, command in (
            (["ui"], "ui"),
            (["setup"], "setup"),
            (["check"], "check"),
            (["cli", "--", "--help"], "cli"),
            (["run", "--", "python3", "-V"], "run"),
        ):
            with self.subTest(command=command):
                self.assertEqual(command, parser.parse_args(arguments).command)

    def test_status_reports_only_availability(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = UserConfigSecretProvider(Path(directory) / "credentials.json")
            self.assertEqual({"configured": False}, credential_status(provider))
            provider.save_token("status-private-synthetic")
            self.assertEqual({"configured": True}, credential_status(provider))
            self.assertNotIn("status-private-synthetic", json.dumps(credential_status(provider)))

    def test_hidden_setup_saves_without_echoing_token(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = UserConfigSecretProvider(Path(directory) / "credentials.json")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = run_hidden_setup(provider, lambda _: "hidden-private-synthetic")
            self.assertEqual(0, result)
            self.assertEqual("hidden-private-synthetic", provider.get_token())
            self.assertNotIn("hidden-private-synthetic", output.getvalue())


class SetupServerTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        path = Path(self.temporary.name) / "processon" / "credentials.json"
        self.provider = UserConfigSecretProvider(path)
        self.launches = []
        self.server, self.url = create_setup_server(
            self.provider, launch_codex=lambda: self.launches.append("codex") or True
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(self, path="/", *, data=None, headers=None):
        request = urllib.request.Request(
            self.url.rstrip("/") + path,
            data=data,
            headers=headers or {},
            method="POST" if data is not None else "GET",
        )
        return urllib.request.urlopen(request, timeout=2)

    def test_server_binds_loopback_and_sets_security_headers(self):
        self.assertEqual("127.0.0.1", self.server.server_address[0])
        with self.request() as response:
            self.assertEqual("no-store", response.headers["Cache-Control"])
            self.assertEqual("no-referrer", response.headers["Referrer-Policy"])
            self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])

    def test_valid_save_returns_boolean_only_and_never_echoes_token(self):
        token = "http-private-synthetic"
        body = json.dumps({"token": token}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Origin": self.url.rstrip("/"),
            "X-CSRF-Token": self.server.csrf_token,
        }
        with self.request("/api/credentials", data=body, headers=headers) as response:
            response_body = response.read().decode("utf-8")
            self.assertEqual({"ok": True}, json.loads(response_body))
            self.assertNotIn(token, response_body)
            self.assertNotIn(token, str(response.headers))
        self.assertEqual(token, self.provider.get_token())

    def test_save_rejects_wrong_origin_csrf_and_content_type(self):
        valid = {
            "Content-Type": "application/json",
            "Origin": self.url.rstrip("/"),
            "X-CSRF-Token": self.server.csrf_token,
        }
        cases = (
            {**valid, "Origin": "http://example.com"},
            {**valid, "X-CSRF-Token": "wrong"},
            {**valid, "Content-Type": "text/plain"},
        )
        for headers in cases:
            with self.subTest(headers=list(headers)):
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    self.request(
                        "/api/credentials",
                        data=b'{"token":"rejected-synthetic"}',
                        headers=headers,
                    )
                self.assertIn(caught.exception.code, {400, 403, 415})
                caught.exception.close()

    def test_save_rejects_empty_and_oversized_body(self):
        headers = {
            "Content-Type": "application/json",
            "Origin": self.url.rstrip("/"),
            "X-CSRF-Token": self.server.csrf_token,
        }
        for body in (b"", b"x" * 8193):
            with self.subTest(length=len(body)):
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    self.request("/api/credentials", data=body, headers=headers)
                self.assertEqual(400, caught.exception.code)
                caught.exception.close()

    def test_launch_requires_same_security_contract_and_opens_codex(self):
        body = b"{}"
        headers = {
            "Content-Type": "application/json",
            "Origin": self.url.rstrip("/"),
            "X-CSRF-Token": self.server.csrf_token,
        }
        with self.request("/api/launch", data=body, headers=headers) as response:
            self.assertEqual({"ok": True}, json.loads(response.read()))
        self.assertEqual(["codex"], self.launches)


if __name__ == "__main__":
    unittest.main()
