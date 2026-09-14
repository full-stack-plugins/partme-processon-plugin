"""Safe stdio-to-Streamable-HTTP proxy for the official ProcessOn MCP."""

from __future__ import annotations

import json
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any, Callable, TextIO

from .setup_trigger import launch_setup_ui_once


PROTOCOL_VERSION = "2025-06-18"
DEFAULT_ENDPOINT = "https://smart-hd.processon.com/mcp"
SESSION_HEADER = "Mcp-Session-Id"
# Generation outlasts a read-only round trip and cannot be replayed, so writes
# get the same budget the diagnostic smoke client uses for tools/call.
GENERATION_TIMEOUT = 180.0
READ_TIMEOUT = 30.0


class ProxyError(RuntimeError):
    """A sanitized proxy error with a stable machine-readable code."""

    def __init__(self, data_code: str, message: str) -> None:
        super().__init__(message)
        self.data_code = data_code
        self.safe_message = message


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_endpoint(endpoint: str) -> None:
    parsed = urllib.parse.urlparse(endpoint)
    if endpoint == DEFAULT_ENDPOINT:
        return
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "127.0.0.1",
        "::1",
        "localhost",
    }:
        raise ValueError("ProcessOn proxy endpoint must be official or loopback")


def parse_streamable_messages(content_type: str, body: bytes) -> list[dict[str, Any]]:
    """Parse JSON or SSE Streamable HTTP payloads into JSON-RPC objects."""
    try:
        text = body.decode("utf-8")
        if "text/event-stream" not in content_type.lower():
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError
            return [payload]
        messages: list[dict[str, Any]] = []
        for line in text.splitlines():
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data or data == "[DONE]":
                continue
            payload = json.loads(data)
            if not isinstance(payload, dict):
                raise ValueError
            messages.append(payload)
        if not messages:
            raise ValueError
        return messages
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ProxyError(
            "PROCESSON_UPSTREAM_ERROR", "ProcessOn returned an invalid MCP response"
        ) from exc


def is_write_like(request: Mapping[str, Any]) -> bool:
    """Treat every MCP tool call as write-like because tools are open-ended."""
    return request.get("method") == "tools/call"


def sanitize_rpc_error(
    request_id: object, code: int, message: str, data_code: str
) -> dict[str, Any]:
    """Build a JSON-RPC error containing only controlled safe fields."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message, "data": {"code": data_code}},
    }


def business_authentication_failed(messages: list[dict[str, Any]]) -> bool:
    """Return whether ProcessOn encoded invalid authentication as tool content."""
    for message in messages:
        result = message.get("result")
        if not isinstance(result, dict):
            continue
        content = result.get("content", [])
        text = " ".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ).strip().lower()
        if text in {"token is invalid", "invalid token", "token invalid"}:
            return True
    return False


def tool_names(payload: Mapping[str, Any]) -> list[str]:
    """Extract valid tool names from one tools/list response."""
    result = payload.get("result", {})
    tools = result.get("tools", []) if isinstance(result, dict) else []
    return [
        tool["name"]
        for tool in tools
        if isinstance(tool, dict) and isinstance(tool.get("name"), str)
    ]


class ProcessOnTransport:
    """Forward one JSON-RPC request to ProcessOn with safe session state."""

    def __init__(
        self,
        endpoint: str,
        provider: object,
        timeout: float = READ_TIMEOUT,
        write_timeout: float = GENERATION_TIMEOUT,
        authentication_required_handler: Callable[[], object] = launch_setup_ui_once,
    ) -> None:
        _validate_endpoint(endpoint)
        self.endpoint = endpoint
        self.provider = provider
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.authentication_required_handler = authentication_required_handler
        self.session_id: str | None = None
        self._opener = urllib.request.build_opener(_NoRedirect())

    def send(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        token = self.provider.get_token()
        if token is None:
            self._request_authentication()
            raise ProxyError(
                "PROCESSON_SETUP_REQUIRED", "ProcessOn setup is required"
            )
        for authentication_attempt in range(2):
            try:
                messages = self._send_once(request, token)
            except urllib.error.HTTPError as exc:
                exc.close()
                if exc.code == 401 and authentication_attempt == 0:
                    self.provider.clear_cache()
                    token = self.provider.get_token()
                    if token is None:
                        self._request_authentication()
                        raise ProxyError(
                            "PROCESSON_AUTH_REQUIRED",
                            "ProcessOn authentication must be configured again",
                        ) from None
                    continue
                if exc.code == 401:
                    self._request_authentication()
                    raise ProxyError(
                        "PROCESSON_AUTH_REQUIRED",
                        "ProcessOn authentication must be configured again",
                    ) from None
                self._raise_upstream_failure(request)
            except (TimeoutError, socket.timeout, urllib.error.URLError, OSError):
                self._raise_upstream_failure(request)
            if business_authentication_failed(messages):
                self._request_authentication()
                raise ProxyError(
                    "PROCESSON_AUTH_REQUIRED",
                    "ProcessOn authentication must be configured again",
                )
            return messages
        self._request_authentication()
        raise ProxyError(
            "PROCESSON_AUTH_REQUIRED", "ProcessOn authentication must be configured again"
        )

    def _request_authentication(self) -> None:
        """Best-effort local setup launch that never masks the safe proxy error."""
        try:
            self.authentication_required_handler()
        except Exception:
            pass

    def _send_once(self, request: dict[str, Any], token: str) -> list[dict[str, Any]]:
        body = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
        }
        if self.session_id:
            headers[SESSION_HEADER] = self.session_id
        upstream = urllib.request.Request(
            self.endpoint, data=body, headers=headers, method="POST"
        )
        with self._opener.open(upstream, timeout=self._timeout_for(request)) as response:
            response_body = response.read()
            session_id = response.headers.get(SESSION_HEADER)
            if session_id:
                self.session_id = session_id
            if response.status == 202 and not response_body:
                return []
            if not response_body:
                raise ProxyError(
                    "PROCESSON_UPSTREAM_ERROR",
                    "ProcessOn returned an empty MCP response",
                )
            return parse_streamable_messages(
                response.headers.get("Content-Type", "application/json"), response_body
            )

    def _timeout_for(self, request: Mapping[str, Any]) -> float:
        return self.write_timeout if is_write_like(request) else self.timeout

    @staticmethod
    def _raise_upstream_failure(request: Mapping[str, Any]) -> None:
        if is_write_like(request):
            raise ProxyError(
                "UNKNOWN_WRITE_RESULT",
                "ProcessOn generation status is unknown; reconcile before retrying",
            ) from None
        raise ProxyError(
            "PROCESSON_UPSTREAM_ERROR", "ProcessOn MCP is temporarily unavailable"
        ) from None


class ProcessOnProxy:
    """Validate stdio input and map transport failures to JSON-RPC errors."""

    def __init__(self, transport: ProcessOnTransport) -> None:
        self.transport = transport

    def handle_line(self, line: str) -> list[dict[str, Any]]:
        request_id: object = None
        try:
            request = json.loads(line)
            if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
                raise ValueError
            request_id = request.get("id")
        except (json.JSONDecodeError, ValueError):
            return [
                sanitize_rpc_error(
                    None, -32600, "Invalid JSON-RPC request", "INVALID_JSON_RPC"
                )
            ]
        try:
            return self.transport.send(request)
        except ProxyError as exc:
            if "id" not in request:
                return []
            return [sanitize_rpc_error(request_id, -32000, exc.safe_message, exc.data_code)]


def run_stdio(proxy: ProcessOnProxy, stdin: TextIO, stdout: TextIO) -> int:
    """Run a newline-delimited JSON-RPC proxy until stdin closes."""
    for line in stdin:
        if not line.strip():
            continue
        for message in proxy.handle_line(line):
            stdout.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")))
            stdout.write("\n")
            stdout.flush()
    return 0


def main() -> int:
    from .secrets import platform_secret_provider

    proxy = ProcessOnProxy(
        ProcessOnTransport(DEFAULT_ENDPOINT, platform_secret_provider())
    )
    return run_stdio(proxy, sys.stdin, sys.stdout)
