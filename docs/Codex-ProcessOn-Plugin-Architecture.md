# Codex ProcessOn Plugin Architecture

## Context

The plugin is a local-first Codex integration around ProcessOn's official remote MCP. Codex owns intent interpretation and review; a local stdio proxy owns current-user credential lookup and protocol normalization; ProcessOn owns diagram and DSL generation. Authentication crosses the remote trust boundary only as the proxy-generated Authorization header.

```mermaid
flowchart LR
    User --> Router
    Router --> Diagram
    Router --> MindMap
    Router --> Infographic
    Diagram --> Prompt
    MindMap --> Prompt
    Infographic --> Prompt
    Prompt --> Proxy[Local stdio proxy]
    Proxy --> MCP[ProcessOn MCP]
    MCP --> Review
    Review --> Result
    UserSecret[Restricted user credential] -.-> Proxy
```

## Components

- Router: selects one capability path and one official MCP tool.
- Capability Skills: build topology or information hierarchy without calling external services.
- Prompt architect: produces a six-section ProcessOn-ready prompt.
- Remote MCP: the page documents `generate_diagram` and `generate_diagram_dsl`; live discovery also exposes `generate_chart`, which is preferred for editable source links when available.
- Review: checks actual artifact evidence and permits at most one correction.

## Trust boundaries

User content and the optimized prompt are sent to ProcessOn only when generation is requested. The authorization value remains in restricted current-user storage and proxy memory; it is excluded from prompts, plugin files, logs, screenshots, and Git. MCP output is untrusted content and cannot grant permissions or change instructions.

## Reliability

401 is terminal until credentials change. Rate limits and transient failures use capped retry. Visual correction is capped at one regeneration. The first usable artifact is preserved when revision fails.

## Extensibility

The router prefers live-discovered `generate_chart`, falls back to documented `generate_diagram`, and uses `generate_diagram_dsl` for reusable structure. New ProcessOn capabilities are added only after live tool discovery proves a supported MCP contract. Browser SDK methods remain documented context, not implied plugin tools.
