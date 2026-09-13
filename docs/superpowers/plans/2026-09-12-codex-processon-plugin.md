# Codex ProcessOn Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a Codex plugin that uses ProcessOn's official remote MCP server and focused Skills to generate polished, editable professional diagrams, mind maps, and infographics.

**Architecture:** A Codex compatibility manifest packages six focused Skills and one Streamable HTTP MCP connection. The router classifies user intent, the prompt layer adds diagram-specific structure and visual constraints, the official ProcessOn MCP performs generation, and the review layer applies one bounded quality-revision cycle.

**Tech Stack:** Codex plugin compatibility manifest, Agent Skills Markdown, MCP Streamable HTTP `2025-06-18`, JSON, Python 3 standard library tests and validators, Pillow/CairoSVG or macOS image tooling for deterministic logo derivatives, Git.

**Spec:** `docs/superpowers/specs/2026-09-12-codex-processon-plugin-design.md`

## Global Constraints

- Plugin root and manifest name are exactly `codex-processon-plugin`.
- The official MCP endpoint is exactly `https://smart-hd.processon.com/mcp`.
- Authentication uses `env_http_headers` to map `Authorization` to `PROCESSON_MCP_AUTHORIZATION`; the environment value is the complete `Bearer <token>` header value.
- No ProcessOn token may appear in tracked or untracked repository files, test output, documentation, screenshots, or Git history.
- The documented server supports MCP version `2025-06-18` and earlier and is limited to 600 requests per token per minute.
- Current required remote tools are `generate_diagram` and `generate_diagram_dsl`.
- `/Users/wandl/Downloads/logo_white.svg` is the only logo source; preserve its vector paths and aspect ratio.
- Generation may regenerate at most once after quality review; retries and polling are always bounded.
- Browser automation is excluded from the default runtime path.
- Use the user's language for prompts and results.
- Do not reduce architecture diagrams to directory trees.

---

## File Map

| Path | Responsibility |
|---|---|
| `.codex-plugin/plugin.json` | Plugin identity, presentation metadata, Skill and MCP discovery |
| `.mcp.json` | Official ProcessOn Streamable HTTP MCP connection and environment-backed authorization |
| `.agents/plugins/marketplace.json` | Repository marketplace entry for Codex discovery |
| `skills/codex-processon-use/SKILL.md` | Public intent router and orchestration contract |
| `skills/codex-processon-diagram/SKILL.md` | Professional and technical diagram modeling |
| `skills/codex-processon-mindmap/SKILL.md` | Knowledge hierarchy and mind-map modeling |
| `skills/codex-processon-infographic/SKILL.md` | Information relationship to visual-layout mapping |
| `skills/codex-processon-prompt/SKILL.md` | ProcessOn-ready prompt construction contract |
| `skills/codex-processon-review/SKILL.md` | Semantic and visual quality gate |
| `assets/logo.svg` | Exact copy of the approved source SVG |
| `assets/logo.png` | Plugin directory light-surface logo |
| `assets/logo-dark.png` | Plugin directory dark-surface logo |
| `assets/composer-icon.png` | Compact composer icon |
| `scripts/generate_assets.py` | Deterministic source-SVG validation and PNG derivative generation |
| `scripts/validate_distribution.py` | Whole-package structural, reference, credential, and documentation validator |
| `scripts/mcp_smoke_test.py` | Redacted MCP initialize, tools/list, and bounded test-call client |
| `tests/test_manifest.py` | Manifest, MCP, and marketplace contract tests |
| `tests/test_skills.py` | Skill frontmatter, routing, quality, and safety contract tests |
| `tests/test_assets.py` | Logo provenance, format, dimensions, and reference tests |
| `tests/test_docs.py` | Upstream documentation-index completeness tests |
| `tests/test_security.py` | Secret-pattern and unsafe configuration tests |
| `tests/test_mcp_smoke.py` | Offline unit tests for MCP request/response parsing and redaction |
| `docs/ProcessOn-Documentation-Index.zh_CN.md` | Complete visible AI, DSL, and MCP documentation index |
| `README.md`, `README.zh-CN.md` | Installation, configuration, use cases, examples, and troubleshooting |
| `docs/Codex-ProcessOn-Plugin-Architecture*.md` | Bilingual architecture documentation |
| `docs/Codex-ProcessOn-Plugin-Technical-Solution*.md` | Bilingual implementation and operational documentation |
| `PRIVACY.md`, `TERMS.md`, `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md` | Distribution and policy materials |

---

### Task 1: Package Manifest and Remote MCP Contract

**Files:**
- Create: `.codex-plugin/plugin.json`
- Create: `.mcp.json`
- Create: `.agents/plugins/marketplace.json`
- Create: `tests/test_manifest.py`
- Create: `.gitignore`

**Interfaces:**
- Consumes: approved design spec and Codex compatibility manifest schema.
- Produces: plugin identity `codex-processon-plugin`; MCP server key `processon`; environment variable `PROCESSON_MCP_AUTHORIZATION`.

- [x] **Step 1: Write failing manifest contract tests**

```python
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ManifestContractTest(unittest.TestCase):
    def test_plugin_and_mcp_contract(self):
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        mcp = json.loads((ROOT / ".mcp.json").read_text())
        self.assertEqual("codex-processon-plugin", plugin["name"])
        self.assertEqual("./skills/", plugin["skills"])
        self.assertEqual("./.mcp.json", plugin["mcpServers"])
        server = mcp["mcpServers"]["processon"]
        self.assertEqual("http", server["type"])
        self.assertEqual("https://smart-hd.processon.com/mcp", server["url"])
        self.assertEqual(
            "PROCESSON_MCP_AUTHORIZATION",
            server["env_http_headers"]["Authorization"],
        )

    def test_marketplace_entry_matches_plugin(self):
        marketplace = json.loads(
            (ROOT / ".agents/plugins/marketplace.json").read_text()
        )
        entry = marketplace["plugins"][0]
        self.assertEqual("codex-processon-plugin", entry["name"])
        self.assertEqual("AVAILABLE", entry["policy"]["installation"])
        self.assertEqual("ON_USE", entry["policy"]["authentication"])
        self.assertEqual("Creativity", entry["category"])
```

- [x] **Step 2: Run the tests and verify the missing files fail**

Run: `python3 -m unittest tests.test_manifest -v`

Expected: FAIL with `FileNotFoundError` for `.codex-plugin/plugin.json`.

- [x] **Step 3: Scaffold the compatibility package and fill exact metadata**

Run the local `plugin-creator` scaffold without overwriting the approved spec:

```bash
python3 /Users/wandl/.codex/skills/.system/plugin-creator/scripts/create_basic_plugin.py \
  codex-processon-plugin \
  --path /Users/wandl/workspaces/workspace-partme-ai \
  --with-skills --with-assets --with-mcp --force
```

Then use `apply_patch` to set the manifest to version `0.1.0`, category `Creativity`, MCP path `./.mcp.json`, developer `Full Stack Skills / PartMe.AI`, ProcessOn website URLs, three concise default prompts, brand color `#2F80ED`, and the four asset paths from the file map. Create `.mcp.json` with exactly:

```json
{
  "mcpServers": {
    "processon": {
      "type": "http",
      "url": "https://smart-hd.processon.com/mcp",
      "env_http_headers": {
        "Authorization": "PROCESSON_MCP_AUTHORIZATION"
      }
    }
  }
}
```

Create the marketplace with name `partme-ai-processon`, display name `PartMe.AI ProcessOn`, an `AVAILABLE`/`ON_USE` Creativity entry, and a Git URL source `https://github.com/partme-ai/codex-processon-plugin.git` on `main`, matching the established standalone sibling-plugin convention. Add `.DS_Store`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.agents/cache/`, and `artifacts/acceptance/` to `.gitignore`.

- [x] **Step 4: Run manifest tests and plugin validator**

Run:

```bash
python3 -m unittest tests.test_manifest -v
python3 /Users/wandl/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Expected: both manifest tests PASS; plugin validation may still report the not-yet-created declared asset files, which is the explicit red state carried into Task 2.

- [x] **Step 5: Commit the package contract**

```bash
git add .codex-plugin/plugin.json .mcp.json .agents/plugins/marketplace.json .gitignore tests/test_manifest.py
git commit -m "feat: define processon plugin package contract"
```

---

### Task 2: Approved Logo Assets

**Files:**
- Create: `assets/logo.svg`
- Create: `assets/logo.png`
- Create: `assets/logo-dark.png`
- Create: `assets/composer-icon.png`
- Create: `scripts/generate_assets.py`
- Create: `tests/test_assets.py`

**Interfaces:**
- Consumes: `/Users/wandl/Downloads/logo_white.svg` and manifest asset paths from Task 1.
- Produces: deterministic transparent PNGs at 512x512, 512x512, and 64x64 while preserving the original SVG bytes at `assets/logo.svg`.

- [x] **Step 1: Write failing provenance and image tests**

```python
import hashlib
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/Users/wandl/Downloads/logo_white.svg")


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"not PNG: {path}")
    return struct.unpack(">II", data[16:24])


class AssetContractTest(unittest.TestCase):
    def test_svg_is_exact_approved_source(self):
        self.assertEqual(
            hashlib.sha256(SOURCE.read_bytes()).digest(),
            hashlib.sha256((ROOT / "assets/logo.svg").read_bytes()).digest(),
        )

    def test_png_dimensions(self):
        self.assertEqual((512, 512), png_size(ROOT / "assets/logo.png"))
        self.assertEqual((512, 512), png_size(ROOT / "assets/logo-dark.png"))
        self.assertEqual((64, 64), png_size(ROOT / "assets/composer-icon.png"))
```

- [x] **Step 2: Run the asset tests and verify they fail**

Run: `python3 -m unittest tests.test_assets -v`

Expected: FAIL because `assets/logo.svg` and PNG derivatives do not exist.

- [x] **Step 3: Implement deterministic asset generation**

Implement `scripts/generate_assets.py` with the exact public signatures `validate_svg(source: Path) -> tuple[int, int]`, `copy_source_svg(source: Path, destination: Path) -> None`, `render_square_png(source: Path, destination: Path, size: int, background: str) -> None`, and `generate_assets(source: Path, assets_dir: Path) -> None`.

The script must reject missing SVG/viewBox data, copy source bytes unchanged, render the white mark on ProcessOn blue `#2F80ED` for `logo.png`, on near-black `#111827` for `logo-dark.png`, and on ProcessOn blue for `composer-icon.png`. Use an already-installed SVG renderer when available; otherwise fail with an actionable dependency message instead of downloading software silently.

Run:

```bash
python3 scripts/generate_assets.py /Users/wandl/Downloads/logo_white.svg assets
```

- [x] **Step 4: Verify assets and plugin validation pass**

Run:

```bash
python3 -m unittest tests.test_assets tests.test_manifest -v
python3 /Users/wandl/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Expected: all tests PASS and validator prints a successful result.

- [x] **Step 5: Commit the brand assets**

```bash
git add assets scripts/generate_assets.py tests/test_assets.py
git commit -m "feat: add approved processon brand assets"
```

---

### Task 3: Router, Prompt, and Quality-Review Skills

**Files:**
- Create: `skills/codex-processon-use/SKILL.md`
- Create: `skills/codex-processon-prompt/SKILL.md`
- Create: `skills/codex-processon-review/SKILL.md`
- Create: `tests/test_skills.py`

**Interfaces:**
- Consumes: MCP tool names from Task 1.
- Produces: route labels `diagram`, `mindmap`, `infographic`; generation modes `visual` and `dsl`; review verdicts `PASS` and `REVISE_ONCE`.

- [x] **Step 1: Write failing router and safety tests**

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def read_skill(self, name: str) -> str:
        return (ROOT / "skills" / name / "SKILL.md").read_text()

    def test_router_names_every_route_and_tool(self):
        text = self.read_skill("codex-processon-use")
        for value in (
            "codex-processon-diagram",
            "codex-processon-mindmap",
            "codex-processon-infographic",
            "generate_diagram",
            "generate_diagram_dsl",
        ):
            self.assertIn(value, text)

    def test_review_is_bounded(self):
        text = self.read_skill("codex-processon-review")
        self.assertIn("REVISE_ONCE", text)
        self.assertIn("at most one", text.lower())

    def test_secrets_are_not_echoed(self):
        combined = "\n".join(
            self.read_skill(name)
            for name in (
                "codex-processon-use",
                "codex-processon-prompt",
                "codex-processon-review",
            )
        )
        self.assertIn("never display", combined.lower())
        self.assertIn("PROCESSON_MCP_AUTHORIZATION", combined)
```

- [x] **Step 2: Run the tests and verify missing Skills fail**

Run: `python3 -m unittest tests.test_skills -v`

Expected: FAIL with `FileNotFoundError` for `skills/codex-processon-use/SKILL.md`.

- [x] **Step 3: Implement the three orchestration Skills**

Write complete frontmatter and instructions. The router must select one route, ask only structure-changing questions, call the prompt Skill, choose `generate_diagram` by default or `generate_diagram_dsl` for DSL/review/debug requests, invoke review, permit one `REVISE_ONCE`, and deliver accessible results. The prompt Skill must emit a structured prompt with `Intent`, `Content`, `Relationships`, `Layout`, `Visual system`, and `Constraints`. The review Skill must score semantic completeness, relationship correctness, visual hierarchy, readability, layout fit, consistency, and editability, and output one of:

```text
PASS
REVISE_ONCE: <specific defects and corrected prompt constraints>
```

- [x] **Step 4: Validate the three Skills**

Run:

```bash
python3 -m unittest tests.test_skills -v
for skill in skills/codex-processon-use skills/codex-processon-prompt skills/codex-processon-review; do
  python3 /Users/wandl/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$skill"
done
```

Expected: tests and all three Skill validators PASS.

- [x] **Step 5: Commit orchestration Skills**

```bash
git add skills/codex-processon-use skills/codex-processon-prompt skills/codex-processon-review tests/test_skills.py
git commit -m "feat: add processon routing and quality workflow"
```

---

### Task 4: Diagram, Mind-Map, and Infographic Skills

**Files:**
- Create: `skills/codex-processon-diagram/SKILL.md`
- Create: `skills/codex-processon-mindmap/SKILL.md`
- Create: `skills/codex-processon-infographic/SKILL.md`
- Modify: `tests/test_skills.py`

**Interfaces:**
- Consumes: structured prompt contract from `codex-processon-prompt`.
- Produces: diagram-specific structure models and constraints consumed by the router and review Skills.

- [x] **Step 1: Add failing coverage tests for supported families**

```python
    def test_diagram_skill_covers_professional_families(self):
        text = self.read_skill("codex-processon-diagram")
        for value in ("flowchart", "swimlane", "sequence", "architecture", "ER", "UML", "SWOT", "PEST"):
            self.assertIn(value.lower(), text.lower())

    def test_mindmap_skill_defines_seven_structures(self):
        text = self.read_skill("codex-processon-mindmap")
        for value in ("mind_free", "mind_right", "mind_org", "mind_ishikawa_left", "mind_timeline_h", "mind_tree_free", "mind_treeTable_left_title"):
            self.assertIn(value, text)

    def test_infographic_skill_maps_relationships_to_layout(self):
        text = self.read_skill("codex-processon-infographic")
        for value in ("comparison", "cycle", "matrix", "ring", "staircase", "radial"):
            self.assertIn(value, text.lower())
```

- [x] **Step 2: Run the focused tests and verify failure**

Run: `python3 -m unittest tests.test_skills.SkillContractTest.test_diagram_skill_covers_professional_families tests.test_skills.SkillContractTest.test_mindmap_skill_defines_seven_structures tests.test_skills.SkillContractTest.test_infographic_skill_maps_relationships_to_layout -v`

Expected: FAIL because the three capability Skills do not exist.

- [x] **Step 3: Implement all three capability Skills**

Each Skill must define triggers, required input model, default decisions, diagram-specific notation, prompt constraints, error boundaries, and handoff to prompt/review. Preserve these exact mind-map structure identifiers and explain that the current MCP exposes a natural-language `prompt`, so identifiers become prompt constraints rather than invented MCP parameters.

- [x] **Step 4: Validate all six Skills**

Run:

```bash
python3 -m unittest tests.test_skills -v
for skill in skills/*; do
  python3 /Users/wandl/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$skill"
done
```

Expected: all Skill tests and six validators PASS.

- [x] **Step 5: Commit capability Skills**

```bash
git add skills/codex-processon-diagram skills/codex-processon-mindmap skills/codex-processon-infographic tests/test_skills.py
git commit -m "feat: add professional processon diagram skills"
```

---

### Task 5: Complete Documentation Index and Bilingual Delivery Docs

**Files:**
- Create: `docs/ProcessOn-Documentation-Index.zh_CN.md`
- Create: `docs/Codex-ProcessOn-Plugin-Architecture.md`
- Create: `docs/Codex-ProcessOn-Plugin-Architecture.zh_CN.md`
- Create: `docs/Codex-ProcessOn-Plugin-Technical-Solution.md`
- Create: `docs/Codex-ProcessOn-Plugin-Technical-Solution.zh_CN.md`
- Create: `README.md`
- Create: `README.zh-CN.md`
- Create: `tests/test_docs.py`

**Interfaces:**
- Consumes: upstream documentation inventory and implemented package/Skill behavior.
- Produces: auditable documentation index and user-facing installation/usage contract.

- [x] **Step 1: Write failing documentation coverage tests**

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTest(unittest.TestCase):
    def test_index_lists_all_primary_sections(self):
        text = (ROOT / "docs/ProcessOn-Documentation-Index.zh_CN.md").read_text()
        required = (
            "生成可编辑图形", "生成图片", "多渲染实例", "错误处理示例",
            "在 Vue 中使用", "在 React 中使用", "初始化", "创建图表",
            "创建图片", "更新图表", "停止请求", "事件监听", "渲染已有数据",
            "视觉信息图能力", "实例管理", "渲染实例方法", "申请Token",
            "MCP 配置", "各平台接入教程", "错误码说明", "MCP Client 推荐",
            "LLM 推荐", "工具列表", "接口说明", "版本日志",
        )
        for heading in required:
            self.assertIn(heading, text)

    def test_readmes_document_runtime_secret(self):
        for name in ("README.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text()
            self.assertIn("PROCESSON_MCP_AUTHORIZATION", text)
            self.assertIn("Bearer ", text)
```

- [x] **Step 2: Run documentation tests and verify failure**

Run: `python3 -m unittest tests.test_docs -v`

Expected: FAIL because the documentation index and READMEs do not exist.

- [x] **Step 3: Write the complete documentation index**

List every visible AI page entry under Overview, Quick Start, Complete Examples, API Reference, FAQ, and Best Practices; every visible MCP entry from Token application through version log; and the visible DSL groups for common syntax, style syntax, infographic, organization, pyramid, and timeline. Record source URLs and the 2026-09-12 observation date. Summarize contracts without copying long source passages.

- [x] **Step 4: Write bilingual architecture, solution, and README documents**

Include Mermaid component and sequence diagrams, trust boundary, routing matrix, quality gate, install steps, environment configuration, at least twelve copyable diagram requests, error table, MCP constraints, test commands, privacy statement, and current upstream limitations. Ensure the documents describe only implemented behavior.

- [x] **Step 5: Run documentation tests and link checks**

Run:

```bash
python3 -m unittest tests.test_docs -v
rg -n "TBD|TODO|FIXME|PLACEHOLDER" README.md README.zh-CN.md docs --glob '*.md' --glob '!docs/superpowers/**'
git diff --check
```

Expected: documentation tests PASS; `rg` produces no output; diff check exits successfully.

- [x] **Step 6: Commit documentation**

```bash
git add README.md README.zh-CN.md docs tests/test_docs.py
git commit -m "docs: document processon plugin and upstream contracts"
```

---

### Task 6: Distribution, Security, and MCP Smoke-Test Harness

**Files:**
- Create: `scripts/validate_distribution.py`
- Create: `scripts/mcp_smoke_test.py`
- Create: `tests/test_security.py`
- Create: `tests/test_mcp_smoke.py`
- Create: `PRIVACY.md`
- Create: `TERMS.md`
- Create: `LICENSE`
- Create: `NOTICE`
- Create: `THIRD_PARTY_NOTICES.md`

**Interfaces:**
- Consumes: package files, runtime `PROCESSON_MCP_AUTHORIZATION`, MCP endpoint.
- Produces: `validate_distribution() -> list[str]`; redacted smoke-test JSON with initialized protocol version, discovered tool names, and optional generation result metadata.

- [x] **Step 1: Write failing security and MCP parsing tests**

```python
import unittest
from scripts.mcp_smoke_test import redact, tool_names


class McpSmokeUnitTest(unittest.TestCase):
    def test_redact_removes_bearer_secret(self):
        self.assertEqual("Bearer ***", redact("Bearer test-secret-value"))

    def test_tool_names_extracts_required_tools(self):
        payload = {"result": {"tools": [{"name": "generate_diagram"}, {"name": "generate_diagram_dsl"}]}}
        self.assertEqual(
            {"generate_diagram", "generate_diagram_dsl"},
            set(tool_names(payload)),
        )
```

`tests/test_security.py` must walk repository files excluding `.git`, reject the supplied test-token literal, reject `Authorization: Bearer` followed by a non-placeholder value, and assert `.mcp.json` uses `env_http_headers` rather than a literal `headers` object.

- [x] **Step 2: Run focused tests and verify imports fail**

Run: `python3 -m unittest tests.test_security tests.test_mcp_smoke -v`

Expected: FAIL with `ModuleNotFoundError: scripts.mcp_smoke_test`.

- [x] **Step 3: Implement a bounded, redacted Streamable HTTP client**

Implement the exact public signatures `redact(value: str) -> str`, `encode_rpc(method: str, params: dict, request_id: int) -> bytes`, `parse_streamable_response(content_type: str, body: bytes) -> dict`, `tool_names(payload: dict) -> list[str]`, `initialize(endpoint: str, authorization: str, timeout: float = 30.0) -> tuple[str, dict]`, `list_tools(endpoint: str, authorization: str, session_id: str, timeout: float = 30.0) -> dict`, and `call_tool(endpoint: str, authorization: str, session_id: str, name: str, prompt: str, timeout: float = 180.0) -> dict` using Python standard-library HTTP primitives and JSON parsing.

Use JSON-RPC `2.0`, initialize with protocol version `2025-06-18`, send `notifications/initialized`, preserve the server session header, accept JSON or SSE-framed JSON responses, cap retryable 407/429/5xx attempts at three with exponential backoff and jitter, never retry 401, and print only redacted summaries.

- [x] **Step 4: Implement distribution validation and policy files**

`validate_distribution()` must verify required files, parse JSON, validate manifest-to-file references, validate all six Skills, check PNG signatures/dimensions, check documentation headings, and scan secrets. Return an error list and exit nonzero when it is nonempty. Use Apache-2.0 policy files matching the sibling PartMe.AI plugin convention and disclose that prompts are sent to ProcessOn.

- [x] **Step 5: Run all offline tests and validators**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_distribution.py
python3 /Users/wandl/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
git diff --check
```

Expected: all tests PASS; both validators succeed; diff check is clean.

- [x] **Step 6: Commit validation and policy files**

```bash
git add scripts/validate_distribution.py scripts/mcp_smoke_test.py tests/test_security.py tests/test_mcp_smoke.py PRIVACY.md TERMS.md LICENSE NOTICE THIRD_PARTY_NOTICES.md
git commit -m "test: add processon distribution and mcp validation"
```

---

### Task 7: Live MCP Contract and Three-Diagram Acceptance

**Files:**
- Create at runtime only: `artifacts/acceptance/acceptance-summary.json` (gitignored)
- Modify only if a verified defect is found: files owned by Tasks 1–6

**Interfaces:**
- Consumes: runtime-only `PROCESSON_MCP_AUTHORIZATION`, `scripts/mcp_smoke_test.py`, installed plugin.
- Produces: verified initialization evidence, tool inventory, and three visually inspected ProcessOn artifacts without persisting the credential.

- [x] **Step 1: Confirm the repository contains no credential before live testing**

Run:

```bash
python3 -m unittest tests.test_security -v
git grep -n -I -E 'Bearer[[:space:]]+[A-Za-z0-9+/=_-]{20,}' -- . ':!docs/superpowers/specs/*'
```

Expected: security tests PASS and `git grep` produces no credential match.

- [x] **Step 2: Run MCP initialization and tool discovery with a process-scoped environment value**

Launch the smoke client with the user-provided token supplied only through the current process environment as the complete `Bearer TOKEN_VALUE` value. Do not place the value in shell history, a file, command output, or the plan. The client reads `PROCESSON_MCP_AUTHORIZATION` and prints only protocol version and tool names.

Expected: initialization succeeds with a compatible protocol and `tools/list` contains both `generate_diagram` and `generate_diagram_dsl`.

- [x] **Step 3: Generate the Agent Harness architecture acceptance diagram**

Call `generate_diagram` with a Chinese prompt requiring orchestration, memory, tool gateway, retry/rollback, guardrails, eval pipeline, observability, deployment, trust boundaries, and labeled data/control flows. Require a restrained dark-blue/teal system, clear layers, minimal line crossings, and readable labels.

Expected: accessible ProcessOn result; visual review records PASS for content, hierarchy, boundaries, connectors, contrast, and editability.

- [x] **Step 4: Generate the cross-functional swimlane acceptance diagram**

Call `generate_diagram` with a Chinese prompt for an AI-feature delivery workflow across Product, AI Engineering, Backend, QA, and Operations, including review decisions, model-evaluation failure loop, deployment approval, monitoring, and rollback.

Expected: accessible ProcessOn result; lanes, decisions, exception paths, start/end, and reading direction visibly pass review.

- [x] **Step 5: Generate the structured infographic acceptance diagram**

Call `generate_diagram` with a Chinese prompt for a polished four-quadrant Agent production-readiness infographic covering Quality, Safety, Reliability, and Operations, with restrained color coding, concise metrics, and one center title.

Expected: accessible ProcessOn result; grouping, hierarchy, density, contrast, and content completeness visibly pass review.

- [x] **Step 6: Verify DSL generation separately**

Call `generate_diagram_dsl` for a compact three-layer architecture. Verify the response contains nonempty DSL and that it can be opened or rendered through the returned ProcessOn workflow.

Expected: nonempty reusable DSL and an accessible editor/render result.

- [x] **Step 7: Record redacted acceptance metadata and rerun the full suite**

Write only result URLs/IDs, diagram categories, timestamps, verdicts, and redacted error codes to the gitignored acceptance summary. Never record request headers or the token.

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_distribution.py
python3 /Users/wandl/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
git status --short
```

Expected: all tests and validators PASS; only gitignored runtime artifacts remain outside Git.

---

### Task 8: Install in Codex and Final Completion Audit

**Files:**
- Modify only if necessary after verified install failure: marketplace or manifest files from Task 1
- No credential files

**Interfaces:**
- Consumes: validated repository, repository marketplace, live MCP evidence.
- Produces: Codex-visible installed plugin and requirement-by-requirement completion evidence.

- [x] **Step 1: Inspect available plugin CLI commands before choosing the install path**

Run:

```bash
codex plugin --help
codex plugin marketplace --help
codex plugin list
```

Expected: command output establishes the current supported local marketplace and plugin-install syntax; do not infer syntax from older documentation.

- [x] **Step 2: Add the repository marketplace and install the plugin using the current CLI syntax**

Use the exact local marketplace root and plugin identifier reported as supported by Step 1. If the repository marketplace's Git URL source requires a published remote that does not yet exist, use a temporary local marketplace source pointing at the approved repository for acceptance without changing the committed distributable marketplace. Do not edit global configuration by hand.

Expected: `codex plugin list` shows `codex-processon-plugin` installed from a local source.

- [x] **Step 3: Verify Codex loads Skills and MCP tools in a fresh task**

Start a fresh Codex task, invoke a ProcessOn diagram request, and verify the router Skill and ProcessOn MCP tools are available. Pass authentication through the environment or supported credential UI without storing it in the repository.

Expected: the fresh task identifies the router and can call the two ProcessOn tools.

- [x] **Step 4: Perform the completion audit**

Inspect every explicit requirement in the design spec against files, test output, plugin validator output, installed plugin state, discovered tools, and the three acceptance diagrams. Classify each as proven, contradicted, weak, or missing; fix any contradicted or missing item and repeat validation.

- [x] **Step 5: Commit any verified installation fixes and record final Git evidence**

If installation required a correction, inspect `git diff --name-only`, add only the exact corrected files from `.codex-plugin/plugin.json`, `.mcp.json`, or `.agents/plugins/marketplace.json`, and commit them with `git commit -m "fix: complete codex processon installation"`. If no installation fix was necessary, do not create an empty commit.

Run:

```bash
git status --short --branch
git log --oneline --decorate -8
git rev-parse HEAD
```

Expected: clean worktree, complete commit history, and a recorded local HEAD. Remote publication is a separate action unless the user explicitly authorizes creating/pushing a remote repository.
