# Codex ProcessOn Plugin

Create polished, editable ProcessOn diagrams from Codex through ProcessOn's official remote MCP server. The plugin adds focused workflows for professional diagrams, mind maps, structured infographics, prompt construction, and quality review.

## Capabilities

- ProcessOn flowcharts, swimlanes, sequence diagrams, UML, architecture diagrams, ER diagrams, organization and equity charts, timelines, SWOT, and PEST.
- ProcessOn mind maps, right-oriented logic maps, fishbone analysis, WBS trees, and tree tables.
- ProcessOn comparison, cycle, ring, matrix, staircase, pyramid, and radial infographics.
- Bounded quality review for semantic correctness, relationships, hierarchy, readability, consistency, and editability.
- Direct access to `generate_diagram` and `generate_diagram_dsl` on the official ProcessOn MCP server.

## Authentication

Set the complete authorization header value in the environment that launches Codex:

```bash
export PROCESSON_MCP_AUTHORIZATION="Bearer <your-processon-token>"
```

Create a token at <https://smart.processon.com/user>. Never commit it to this repository or paste it into a diagram prompt.

## Install for local development

Use the current `codex plugin --help` output to confirm supported local-marketplace commands, add this repository marketplace, then install `codex-processon-plugin@partme-ai-processon`. Restart or open a fresh Codex task after installation so new Skills and MCP tools are loaded.

## Example requests

- Create a production Agent Harness architecture diagram with orchestration, memory, tool gateway, guardrails, evals, observability, trust boundaries, and recovery paths.
- Draw a five-lane AI feature delivery workflow with approval, evaluation failure, deployment, monitoring, and rollback.
- Build an ER diagram for tenants, agents, sessions, tool calls, traces, and evaluation results.
- Create a sequence diagram for an agent request that calls RAG, tools, guardrails, and retry logic.
- Turn this incident report into a fishbone root-cause map, separating evidence from hypotheses.
- Build a four-quadrant ProcessOn infographic for Quality, Safety, Reliability, and Operations.

## Behavior

The router selects one diagram family, models the relationships, enriches the ProcessOn prompt, calls the official MCP tool, and reviews the returned artifact. It may perform at most one specific regeneration. A successful call without an accessible artifact is not treated as visual acceptance.

## Upstream constraints

- Endpoint: `https://smart-hd.processon.com/mcp`
- Transport: Streamable HTTP
- Documented protocol ceiling: MCP `2025-06-18`
- Documented rate limit: 600 requests per token per minute
- Current tools: `generate_diagram`, `generate_diagram_dsl`

Live discovery on 2026-09-13 also returned an undocumented `generate_chart` alias. The plugin keeps the two page-documented tools as its stable routing contract.

The AI SDK exposes broader browser integration capabilities, but this plugin does not claim MCP operations that are not actually advertised by the server.

## Development

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python scripts/validate_distribution.py
.venv/bin/python /Users/wandl/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

See [the documentation index](docs/ProcessOn-Documentation-Index.zh_CN.md), [architecture](docs/Codex-ProcessOn-Plugin-Architecture.md), and [technical solution](docs/Codex-ProcessOn-Plugin-Technical-Solution.md).
