import json
import unittest

from scripts.mcp_smoke_test import (
    McpSmokeError,
    SUPPORTED_TOOLS,
    encode_rpc,
    ensure_tool_success,
    parse_streamable_response,
    redact,
    tool_names,
)


class McpSmokeUnitTest(unittest.TestCase):
    def test_redact_removes_bearer_secret(self):
        self.assertEqual("Bearer ***", redact("Bearer test-secret-value"))

    def test_encode_rpc_uses_jsonrpc_contract(self):
        payload = json.loads(encode_rpc("tools/list", {}, 7))
        self.assertEqual(
            {"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {}},
            payload,
        )

    def test_parse_streamable_json_response(self):
        body = b'{"jsonrpc":"2.0","id":2,"result":{"tools":[]}}'
        self.assertEqual([], parse_streamable_response("application/json", body)["result"]["tools"])

    def test_parse_streamable_sse_response(self):
        body = b'event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"tools":[]}}\n\n'
        self.assertEqual(
            [],
            parse_streamable_response("text/event-stream", body)["result"]["tools"],
        )

    def test_tool_names_extracts_required_tools(self):
        payload = {
            "result": {
                "tools": [
                    {"name": "generate_diagram", "description": "Generate a diagram"},
                    {"name": "generate_diagram_dsl", "description": "Generate DSL"},
                ]
            }
        }
        self.assertEqual(
            {"generate_diagram", "generate_diagram_dsl"},
            set(tool_names(payload)),
        )

    def test_business_authentication_failure_is_rejected(self):
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [{"type": "text", "text": "token is Invalid"}],
                "isError": False,
            },
        }
        with self.assertRaisesRegex(McpSmokeError, "authentication failed"):
            ensure_tool_success(payload)

    def test_smoke_client_supports_live_editable_tool(self):
        self.assertIn("generate_chart", SUPPORTED_TOOLS)


if __name__ == "__main__":
    unittest.main()
