# Codex ProcessOn Plugin Technical Solution

## Package contract

`.codex-plugin/plugin.json` declares the Skills, presentation assets, and `.mcp.json`. The MCP configuration maps the `Authorization` header to `PROCESSON_MCP_AUTHORIZATION`; its value is the complete `Bearer <token>` string.

## Request sequence

```mermaid
sequenceDiagram
    participant U as User
    participant R as Router Skill
    participant P as Prompt Skill
    participant M as ProcessOn MCP
    participant Q as Review Skill
    U->>R: Diagram request
    R->>R: Select family and model structure
    R->>P: Structure + audience + style
    P-->>R: Six-section prompt
    R->>M: generate_diagram(prompt)
    M-->>R: Editable/view result
    R->>Q: Request + artifact
    alt Pass
        Q-->>U: PASS + result
    else One correctable defect
        Q-->>R: REVISE_ONCE
        R->>M: One corrected request
        M-->>U: Final result + limitation if any
    end
```

## Error policy

- Missing authorization: stop locally with configuration guidance.
- 401: no retry and no credential echo.
- 407 or equivalent rate limit: capped exponential backoff with jitter.
- Transient connection/5xx: at most three attempts.
- Empty artifact: preserve metadata and allow one correction.

## Validation

Python standard-library tests validate JSON contracts, asset provenance/dimensions, Skill contracts, documentation coverage, secret handling, and MCP parsing. The official plugin validator checks package ingestion. Live acceptance verifies initialize, tools/list, DSL generation, and three visually inspected diagram families.

## Operational limits

The MCP page documents two prompt-only tools, while live discovery on 2026-09-13 returned a third prompt-only tool, `generate_chart`. The plugin prefers that live tool for editable links and retains the documented fallback. Existing-document mutation, account administration, attachment upload, and SDK editor lifecycle operations remain outside the default plugin contract.
