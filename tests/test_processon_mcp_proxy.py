import io
import json
import threading
import time
import unittest
import urllib.error
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from processon_harness.mcp_proxy import (
    ProcessOnProxy,
    ProcessOnTransport,
    ProxyError,
    is_write_like,
    parse_streamable_messages,
    run_stdio,
)


class RotatingProvider:
    def __init__(self, tokens):
        self.tokens = deque(tokens)
        self.current = None
        self.clear_count = 0

    def get_token(self):
        if self.current is None and self.tokens:
            self.current = self.tokens.popleft()
        return self.current

    def clear_cache(self):
        self.clear_count += 1
        self.current = None


class FixtureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        request = json.loads(body)
        self.server.received.append((dict(self.headers.items()), request))
        if self.server.delays:
            time.sleep(self.server.delays.popleft())
        status, headers, response = self.server.responses.popleft()
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        if response:
            self.wfile.write(response)

    def log_message(self, format, *args):
        return None


class ProxyFixture:
    def __init__(self, responses, delays=None):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        self.server.responses = deque(responses)
        self.server.delays = deque(delays or [])
        self.server.received = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        host, port = self.server.server_address
        return self, f"http://{host}:{port}/mcp"

    def __exit__(self, exc_type, exc, traceback):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def json_response(payload):
    return (
        200,
        {"Content-Type": "application/json"},
        json.dumps(payload).encode("utf-8"),
    )


class StreamableResponseTest(unittest.TestCase):
    def test_parses_json_and_sse_messages(self):
        self.assertEqual(
            [{"jsonrpc": "2.0", "id": 1, "result": {}}],
            parse_streamable_messages(
                "application/json", b'{"jsonrpc":"2.0","id":1,"result":{}}'
            ),
        )
        body = (
            b"event: message\n"
            b'data: {"jsonrpc":"2.0","id":2,"result":{"ok":true}}\n\n'
        )
        self.assertEqual(2, parse_streamable_messages("text/event-stream", body)[0]["id"])


class TransportTest(unittest.TestCase):
    def test_injects_bearer_and_preserves_session(self):
        responses = [
            (
                200,
                {"Content-Type": "application/json", "Mcp-Session-Id": "session-1"},
                b'{"jsonrpc":"2.0","id":1,"result":{}}',
            ),
            json_response({"jsonrpc": "2.0", "id": 2, "result": {"tools": []}}),
        ]
        provider = RotatingProvider(["synthetic-token"])
        with ProxyFixture(responses) as (fixture, endpoint):
            transport = ProcessOnTransport(endpoint, provider, timeout=2)
            transport.send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            transport.send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        first_headers = {
            name.lower(): value for name, value in fixture.server.received[0][0].items()
        }
        second_headers = {
            name.lower(): value for name, value in fixture.server.received[1][0].items()
        }
        self.assertEqual("Bearer synthetic-token", first_headers["authorization"])
        self.assertEqual("2025-06-18", first_headers["mcp-protocol-version"])
        self.assertEqual("application/json, text/event-stream", first_headers["accept"])
        self.assertEqual("session-1", second_headers["mcp-session-id"])

    def test_empty_202_notification_emits_no_message(self):
        provider = RotatingProvider(["synthetic-token"])
        with ProxyFixture([(202, {}, b"")]) as (_, endpoint):
            transport = ProcessOnTransport(endpoint, provider, timeout=2)
            messages = transport.send(
                {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
            )
        self.assertEqual([], messages)

    def test_401_reloads_once_then_succeeds(self):
        provider = RotatingProvider(["expired-synthetic", "rotated-synthetic"])
        with ProxyFixture(
            [
                (401, {"Content-Type": "text/plain"}, b"unauthorized"),
                json_response({"jsonrpc": "2.0", "id": 1, "result": {}}),
            ]
        ) as (fixture, endpoint):
            transport = ProcessOnTransport(endpoint, provider, timeout=2)
            messages = transport.send(
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
            )
        self.assertEqual(1, provider.clear_count)
        self.assertEqual(2, len(fixture.server.received))
        self.assertEqual(1, messages[0]["id"])

    def test_second_401_becomes_sanitized_authentication_error(self):
        provider = RotatingProvider(["first-private", "second-private"])
        with ProxyFixture(
            [
                (401, {"Content-Type": "text/plain"}, b"first-private"),
                (401, {"Content-Type": "text/plain"}, b"second-private"),
            ]
        ) as (fixture, endpoint):
            proxy = ProcessOnProxy(ProcessOnTransport(endpoint, provider, timeout=2))
            messages = proxy.handle_line(
                '{"jsonrpc":"2.0","id":8,"method":"initialize","params":{}}'
            )
        encoded = json.dumps(messages)
        self.assertEqual(2, len(fixture.server.received))
        self.assertIn("PROCESSON_AUTH_REQUIRED", encoded)
        self.assertNotIn("first-private", encoded)
        self.assertNotIn("second-private", encoded)

    def test_business_invalid_token_becomes_authentication_error(self):
        provider = RotatingProvider(["private-synthetic"])
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": "token is Invalid"}],
            },
        }
        with ProxyFixture([json_response(payload)]) as (_, endpoint):
            proxy = ProcessOnProxy(ProcessOnTransport(endpoint, provider, timeout=2))
            messages = proxy.handle_line(
                '{"jsonrpc":"2.0","id":3,"method":"tools/call",'
                '"params":{"name":"generate_chart","arguments":{"prompt":"safe"}}}'
            )
        encoded = json.dumps(messages)
        self.assertIn("PROCESSON_AUTH_REQUIRED", encoded)
        self.assertNotIn("token is Invalid", encoded)
        self.assertNotIn("private-synthetic", encoded)

    def test_write_like_server_failure_is_not_retried(self):
        provider = RotatingProvider(["synthetic-token"])
        with ProxyFixture(
            [(500, {"Content-Type": "text/plain"}, b"internal details")]
        ) as (fixture, endpoint):
            proxy = ProcessOnProxy(ProcessOnTransport(endpoint, provider, timeout=2))
            messages = proxy.handle_line(
                '{"jsonrpc":"2.0","id":4,"method":"tools/call",'
                '"params":{"name":"future_generation_tool","arguments":{}}}'
            )
        self.assertEqual(1, len(fixture.server.received))
        self.assertIn("UNKNOWN_WRITE_RESULT", json.dumps(messages))

    def test_write_like_request_gets_the_generation_timeout(self):
        # A real ProcessOn generation was observed to take 12.0s, 27.3s, and to
        # exceed 30s for the same prompt. The short read timeout must not abort
        # the write path, which cannot be safely replayed.
        provider = RotatingProvider(["synthetic-token"])
        responses = [
            json_response({"jsonrpc": "2.0", "id": 6, "result": {"content": []}})
        ]
        with ProxyFixture(responses, delays=[0.6]) as (fixture, endpoint):
            transport = ProcessOnTransport(
                endpoint, provider, timeout=0.2, write_timeout=2.0
            )
            messages = transport.send(
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {"name": "generate_diagram_dsl", "arguments": {}},
                }
            )
        self.assertEqual(1, len(fixture.server.received))
        self.assertEqual(1, len(messages))
        self.assertIn("result", messages[0])

    def test_read_request_keeps_the_short_timeout(self):
        provider = RotatingProvider(["synthetic-token"])
        responses = [
            json_response({"jsonrpc": "2.0", "id": 7, "result": {"tools": []}})
        ]
        with ProxyFixture(responses, delays=[0.6]) as (_, endpoint):
            transport = ProcessOnTransport(
                endpoint, provider, timeout=0.2, write_timeout=2.0
            )
            with self.assertRaises(ProxyError) as caught:
                transport.send(
                    {"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {}}
                )
        self.assertEqual("PROCESSON_UPSTREAM_ERROR", caught.exception.data_code)

    def test_missing_credential_returns_setup_required(self):
        proxy = ProcessOnProxy(ProcessOnTransport("http://127.0.0.1:9/mcp", RotatingProvider([])))
        messages = proxy.handle_line(
            '{"jsonrpc":"2.0","id":5,"method":"tools/list","params":{}}'
        )
        self.assertIn("PROCESSON_SETUP_REQUIRED", json.dumps(messages))
    def test_non_loopback_http_endpoint_is_rejected(self):
        with self.assertRaises(ValueError):
            ProcessOnTransport("http://example.com/mcp", RotatingProvider(["x"]))


class StdioTest(unittest.TestCase):
    def test_malformed_lines_return_safe_json_rpc_errors(self):
        proxy = ProcessOnProxy(ProcessOnTransport("http://127.0.0.1:9/mcp", RotatingProvider([])))
        output = io.StringIO()
        result = run_stdio(proxy, io.StringIO("not-json\n[]\n"), output)
        self.assertEqual(0, result)
        messages = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(2, len(messages))
        self.assertTrue(all(item["error"]["data"]["code"] == "INVALID_JSON_RPC" for item in messages))

    def test_tools_call_is_always_write_like(self):
        self.assertTrue(is_write_like({"method": "tools/call", "params": {"name": "unknown"}}))
        self.assertFalse(is_write_like({"method": "tools/list", "params": {}}))


if __name__ == "__main__":
    unittest.main()
