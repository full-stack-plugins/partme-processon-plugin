# ProcessOn Local Credential Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the plugin's developer-oriented HTTP header configuration with a safe first-use ProcessOn Token setup page and a local stdio MCP proxy that keeps credentials outside the repository and installed plugin cache.

**Architecture:** Codex starts a Python stdio MCP proxy declared by `.mcp.json`. The proxy obtains a raw token from a process override or a restricted current-user credential file, adds exactly one `Bearer ` prefix, and forwards Streamable HTTP JSON-RPC to the official ProcessOn endpoint. A separate loopback-only setup application stores or rotates the token, while a dedicated setup Skill routes missing and invalid credential states into that flow.

**Tech Stack:** Codex plugin manifest, Agent Skills Markdown, MCP Streamable HTTP `2025-06-18`, Python 3 standard library (`argparse`, `getpass`, `http.server`, `json`, `pathlib`, `secrets`, `tempfile`, `urllib`), HTML/CSS/vanilla JavaScript, `unittest`, PyYAML 6.0.3 for distribution validation, Git.

**Spec:** `docs/superpowers/specs/2026-09-14-processon-local-credential-setup-design.md`

**Execution status (2026-09-14):** Tasks 1–7 implemented and locally verified on `main`. Task 8 executed after explicit user authorization: clean-cache installation, MCP discovery, read-only protocol, and one authorized `generate_diagram_dsl` call were all verified, and the acceptance attempt exposed a generation-timeout defect that is fixed locally in `94e3387`. Remote push was deliberately not performed, so the published `main` still carries the defect.

## Global Constraints

- The committed `.mcp.json`, repository, Git history, installed plugin files, test output, setup responses, proxy errors, and logs must not contain a resolved ProcessOn Token.
- Normal users must not edit `.mcp.json`, shell profiles, Codex configuration, or environment variables.
- The normal credential location is current-user state outside the plugin package; plugin upgrades must preserve it.
- `PROCESSON_MCP_TOKEN` is the only advanced process override. It contains the raw token. `PROCESSON_MCP_AUTHORIZATION` is deprecated and removed from the normal runtime contract.
- Unix credential directories are mode `0700`; credential files are mode `0600`. Writes are same-directory, flushed, fsynced, and atomically replaced.
- Reject credential paths through symbolic-link directories and reject non-user-owned directories where ownership APIs are available.
- The setup server binds only to `127.0.0.1`, suppresses access logging, validates Origin and CSRF, limits request bodies, and never returns the submitted token.
- The proxy talks to `https://smart-hd.processon.com/mcp`. Test endpoints are permitted only when loopback.
- Authentication refresh is the only automatic replay. Diagram-generation requests are write-like and must not be automatically replayed after timeout, network failure, HTTP 408, or HTTP 5xx.
- Preserve current official identity: display name `ProcessOn`, official icons, plugin name `codex-processon-plugin`, MCP key `processon`.
- Preserve and integrate the existing uncommitted bilingual README, documentation-test, and `assets/processon-hero.png` work; do not overwrite or discard it.
- Each task starts red, adds the smallest implementation, passes its focused tests, and commits only its owned paths plus deliberate integration edits.
- Before creating or changing Skills, read and apply `skill-creator` and `skill-trace-checker`; run the required TRACE checks before committing Skill changes.
- Do not publish, push, release, delete a user credential, or install into a user Codex environment without a separate explicit instruction for that external-state action.

## File Map

| Path | Responsibility |
|---|---|
| `processon_harness/__init__.py` | Stable package exports without secret values |
| `processon_harness/secrets.py` | Token normalization, lookup priority, safe current-user storage, cache invalidation |
| `processon_harness/mcp_proxy.py` | stdio JSON-RPC loop, Streamable HTTP transport, session handling, safe error mapping |
| `scripts/processon_mcp_proxy.py` | Minimal installed-plugin entry point for the proxy |
| `scripts/processon_setup.py` | Setup UI, hidden terminal setup, status check, and command wrapper CLI |
| `assets/setup/index.html` | Three-step local setup document |
| `assets/setup/styles.css` | ProcessOn-branded responsive setup presentation |
| `assets/setup/app.js` | CSRF-protected save action, input clearing, status messaging |
| `.mcp.json` | Local stdio server declaration with no credential fields |
| `skills/codex-processon-setup/SKILL.md` | First-use, missing-token, invalid-token, and rotation workflow |
| `skills/codex-processon-setup/references/workflow.md` | Exact setup/check/restart verification sequence |
| `skills/codex-processon-setup/references/security.md` | Token handling rules and prohibited disclosure paths |
| `skills/codex-processon-use/SKILL.md` | Router handoff from credential failures to setup Skill |
| `scripts/mcp_smoke_test.py` | Diagnostic client reusing authoritative protocol parsing and safe error rules |
| `tests/test_processon_secrets.py` | Credential normalization, priority, permissions, ownership, and atomicity |
| `tests/test_processon_setup.py` | CLI and loopback setup HTTP security contract |
| `tests/test_processon_mcp_proxy.py` | stdio/HTTP proxy behavior, replay safety, redaction, and session tests |
| `tests/test_manifest.py` | Installed stdio MCP declaration contract |
| `tests/test_security.py` | Repository secret/configuration safety and token-path exclusions |
| `tests/test_skills.py` | Setup Skill discovery, routing, progressive disclosure, and safety |
| `tests/test_mcp_smoke.py` | Shared protocol helper and smoke-client regression tests |
| `scripts/validate_distribution.py` | Complete package, Skill, stdio config, setup asset, and secret validation |
| `README.md`, `README.zh-CN.md` | Bilingual first-use flow, advanced configuration, troubleshooting, and architecture |
| `PRIVACY.md` | Credential location and official ProcessOn data-flow disclosure |

---

### Task 1: Restricted Current-User Credential Provider

**Files:**
- Create: `processon_harness/__init__.py`
- Create: `processon_harness/secrets.py`
- Create: `tests/test_processon_secrets.py`

**Interfaces:**
- `normalize_token(value: str) -> str`
- `default_config_path(environ: Mapping[str, str] | None = None) -> Path`
- `EnvironmentSecretProvider.get_token() -> str | None`
- `UserConfigSecretProvider.get_token() -> str | None`
- `UserConfigSecretProvider.save_token(value: str) -> None`
- `UserConfigSecretProvider.clear_cache() -> None`
- `CompositeSecretProvider.get_token() -> str | None`
- `platform_secret_provider() -> CompositeSecretProvider`

- [ ] **Step 1: Write failing normalization and lookup-priority tests**

Add tests using `tempfile.TemporaryDirectory()` and `unittest.mock.patch.dict` that assert:

```python
self.assertEqual("abc-123", normalize_token("  Bearer abc-123  "))
self.assertEqual("abc-123", normalize_token("abc-123"))
with self.assertRaises(CredentialError):
    normalize_token("line-one\nline-two")
self.assertEqual("env-token", platform_secret_provider().get_token())
```

The environment test must set both a saved synthetic token and `PROCESSON_MCP_TOKEN=env-token` and prove the environment wins without placing either value in an assertion failure message.

- [ ] **Step 2: Run the focused tests and verify the missing package fails**

Run: `python3 -m unittest tests.test_processon_secrets -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'processon_harness'`.

- [ ] **Step 3: Implement normalization, path selection, and provider composition**

Implement exact constants:

```python
TOKEN_KEY = "PROCESSON_MCP_TOKEN"
CONFIG_PATH_OVERRIDE = "PROCESSON_CONFIG_PATH"
DEFAULT_DIRECTORY_NAME = "processon"
DEFAULT_FILE_NAME = "credentials.json"
```

`normalize_token` strips whitespace, removes one case-insensitive leading `Bearer` scheme, rejects empty values, NUL, CR, LF, other ASCII control characters, and values over 8192 characters. `default_config_path` uses the explicit test override first, then `%APPDATA%` on Windows, then `$XDG_CONFIG_HOME`, then `~/.config`. Provider objects cache only in memory for their own process and expose no secret-bearing `repr`.

- [ ] **Step 4: Add failing secure-write and path-defense tests**

Cover:

```python
provider.save_token("Bearer saved-token")
self.assertEqual({"PROCESSON_MCP_TOKEN": "saved-token"}, json.loads(path.read_text()))
self.assertEqual(0o700, stat.S_IMODE(path.parent.stat().st_mode))
self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
```

On Unix, create a symlink for the credential directory and assert save fails. Where `st_uid` is supported, mock or fixture a foreign owner and assert it fails. Patch `os.replace` to prove replacement happens only after flush/fsync and that a failed replacement leaves the previous valid credential readable.

- [ ] **Step 5: Implement atomic restricted storage**

Create the directory with `0700`, re-check non-symlink and owner after creation, create a same-directory temporary file with `0600`, serialize compact UTF-8 JSON, flush, `os.fsync`, `os.replace`, then fsync the directory where supported. Never include the path contents or token in an exception string. Re-open and validate stored JSON as an object with exactly the token key.

- [ ] **Step 6: Run focused tests and commit**

Run:

```bash
python3 -m unittest tests.test_processon_secrets -v
git diff --check
```

Expected: all credential tests PASS.

Commit only these paths:

```bash
git add processon_harness/__init__.py processon_harness/secrets.py tests/test_processon_secrets.py
git commit -m "feat: add secure processon credential storage"
```

---

### Task 2: Safe Streamable HTTP stdio Proxy

**Files:**
- Create: `processon_harness/mcp_proxy.py`
- Create: `scripts/processon_mcp_proxy.py`
- Create: `tests/test_processon_mcp_proxy.py`
- Modify: `scripts/mcp_smoke_test.py`
- Modify: `tests/test_mcp_smoke.py`

**Interfaces:**
- `parse_streamable_messages(content_type: str, body: bytes) -> list[dict[str, Any]]`
- `is_write_like(request: Mapping[str, Any]) -> bool`
- `sanitize_rpc_error(request_id: object, code: int, message: str, data_code: str) -> dict[str, Any]`
- `ProcessOnTransport.send(request: dict[str, Any]) -> list[dict[str, Any]]`
- `ProcessOnProxy.handle_line(line: str) -> list[dict[str, Any]]`
- `run_stdio(proxy: ProcessOnProxy, stdin: TextIO, stdout: TextIO) -> int`

- [ ] **Step 1: Write failing JSON, SSE, session, and empty-notification tests**

Use an in-process `ThreadingHTTPServer` fixture. Assert the fixture receives:

```python
self.assertEqual("Bearer synthetic-token", request_headers["Authorization"])
self.assertEqual("2025-06-18", request_headers["MCP-Protocol-Version"])
self.assertEqual("application/json, text/event-stream", request_headers["Accept"])
```

Return one JSON response, one SSE response, an `Mcp-Session-Id`, and an empty HTTP 202 notification. Assert JSON and SSE become JSON-RPC stdout messages, the next request carries the session ID, and HTTP 202 emits no stdout line.

- [ ] **Step 2: Run proxy tests and verify imports fail**

Run: `python3 -m unittest tests.test_processon_mcp_proxy -v`

Expected: FAIL because `processon_harness.mcp_proxy` does not exist.

- [ ] **Step 3: Implement endpoint validation, parsing, session state, and stdio framing**

Use exact constants:

```python
PROTOCOL_VERSION = "2025-06-18"
DEFAULT_ENDPOINT = "https://smart-hd.processon.com/mcp"
SESSION_HEADER = "Mcp-Session-Id"
```

Accept the official HTTPS origin and loopback HTTP/HTTPS fixtures only. Disable redirects with a custom `HTTPRedirectHandler`. Read one JSON object per stdin line, preserve request IDs, write compact JSON plus one newline, flush after every response, and send diagnostics only as sanitized JSON-RPC errors. Import `parse_streamable_messages`, tool-name extraction, and business-error detection from this module in `scripts/mcp_smoke_test.py` so the proxy and diagnostic client cannot drift.

- [ ] **Step 4: Add failing authentication-refresh and replay-safety tests**

Cover the exact sequences:

- first response 401, provider reloads once, second request succeeds with a rotated synthetic token;
- second 401 stops after two total upstream calls;
- `result.isError=true` plus text `token is Invalid` becomes `PROCESSON_AUTH_REQUIRED` without including upstream text or token;
- `tools/call` for any tool name receives timeout, `URLError`, HTTP 408, and HTTP 500 with exactly one upstream attempt and `UNKNOWN_WRITE_RESULT`;
- `initialize` and `tools/list` return deterministic safe failures and are never looped indefinitely;
- malformed stdin JSON, non-object payload, malformed upstream JSON, and empty non-202 response yield JSON-RPC errors with no request body or credential data.

- [ ] **Step 5: Implement the error taxonomy and no-replay policy**

Use stable safe data codes:

```text
PROCESSON_SETUP_REQUIRED
PROCESSON_AUTH_REQUIRED
PROCESSON_UPSTREAM_ERROR
UNKNOWN_WRITE_RESULT
INVALID_JSON_RPC
```

Treat every `tools/call` as write-like because the ProcessOn tool set is open-ended. Clear only the provider's in-memory cache on 401, reload once, and retry authentication once. Do not retry timeouts, connection failures, 408, 429, or 5xx. Do not serialize exception objects whose representation can contain a URL, header, body, or token.

- [ ] **Step 6: Implement the minimal installed entry point**

`scripts/processon_mcp_proxy.py` adds the plugin root to `sys.path`, creates `platform_secret_provider()`, constructs `ProcessOnProxy` with the official endpoint, and exits with `run_stdio`. It must contain no token lookup logic of its own and write nothing informational to stdout.

- [ ] **Step 7: Run proxy and smoke regressions and commit**

Run:

```bash
python3 -m unittest tests.test_processon_mcp_proxy tests.test_mcp_smoke -v
python3 scripts/processon_mcp_proxy.py </dev/null
git diff --check
```

Expected: tests PASS; empty stdin exits successfully with empty stdout.

Commit:

```bash
git add processon_harness/mcp_proxy.py scripts/processon_mcp_proxy.py scripts/mcp_smoke_test.py tests/test_processon_mcp_proxy.py tests/test_mcp_smoke.py
git commit -m "feat: proxy processon mcp through local stdio"
```

---

### Task 3: Three-Step Loopback Setup Application

**Files:**
- Create: `scripts/processon_setup.py`
- Create: `assets/setup/index.html`
- Create: `assets/setup/styles.css`
- Create: `assets/setup/app.js`
- Create: `tests/test_processon_setup.py`

**Interfaces:**
- `build_parser() -> argparse.ArgumentParser`
- `credential_status(provider: CompositeSecretProvider) -> dict[str, bool]`
- `create_setup_server(provider: UserConfigSecretProvider) -> tuple[ThreadingHTTPServer, str]`
- `run_ui(provider: UserConfigSecretProvider, open_browser: Callable[[str], bool]) -> int`
- `run_hidden_setup(provider: UserConfigSecretProvider, prompt: Callable[[str], str]) -> int`
- `main(argv: Sequence[str] | None = None) -> int`

- [ ] **Step 1: Write failing static UI and command-contract tests**

Assert the HTML has one primary setup card, exactly three numbered steps, a link to `https://smart.processon.com/user`, one `<input type="password">`, and no token placeholder value. Assert commands `ui`, `setup`, `check`, `cli`, and `run --` parse. Test `check` output as exactly a safe availability state such as `ProcessOn credential: configured` or `ProcessOn credential: missing`, never length, prefix, suffix, path contents, or token.

- [ ] **Step 2: Run setup tests and verify missing files fail**

Run: `python3 -m unittest tests.test_processon_setup -v`

Expected: FAIL because `scripts.processon_setup` and setup assets do not exist.

- [ ] **Step 3: Implement the responsive three-step page and CLI skeleton**

Use the official ProcessOn blue palette and existing official icon assets. Keep the page self-contained under `assets/setup/`, accessible at 390x884, 768x1024, and 1280x1024, and free of remote fonts/scripts. `setup` uses `getpass.getpass`; `cli` executes the proxy entry point; `run --` injects only the token into the child process environment and never prints the resulting environment.

- [ ] **Step 4: Add failing HTTP security and secret-non-disclosure tests**

Start the server on an ephemeral port and assert:

- bind host resolves to `127.0.0.1`;
- GET returns CSP, `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, and `X-Content-Type-Options: nosniff`;
- POST rejects missing/wrong Origin, CSRF, JSON content type, empty token, and bodies over 8192 bytes;
- a valid POST saves a synthetic token and returns exactly `{ "ok": true }`;
- response body, headers, captured stdout/stderr, and mocked access logs never contain the synthetic token;
- JavaScript clears the password input in a `finally` path after each save attempt;
- idle timeout calls `shutdown` after ten minutes without using a blocking sleep in tests.

- [ ] **Step 5: Implement hardened HTTP handling and lifecycle**

Generate a per-process CSRF token with `secrets.token_urlsafe`, inject it into the served HTML without adding the credential, require exact Origin matching the selected loopback port, enforce `Content-Length`, parse only a JSON object with string field `token`, and map all errors to short user-safe messages. Override `log_message` to do nothing. Open the browser only after the server is listening. Use a daemon timer for bounded shutdown and cancel it during normal cleanup.

- [ ] **Step 6: Run setup tests and commit**

Run:

```bash
python3 -m unittest tests.test_processon_setup tests.test_processon_secrets -v
python3 scripts/processon_setup.py check
git diff --check
```

Expected: setup and credential tests PASS; `check` returns only configured/missing state.

Commit:

```bash
git add scripts/processon_setup.py assets/setup/index.html assets/setup/styles.css assets/setup/app.js tests/test_processon_setup.py
git commit -m "feat: add local processon token setup"
```

---

### Task 4: Installed Plugin MCP Contract and Distribution Gates

**Files:**
- Modify: `.mcp.json`
- Modify: `tests/test_manifest.py`
- Modify: `tests/test_security.py`
- Modify: `scripts/validate_distribution.py`
- Modify: `tests/test_distribution.py`

**Interfaces:**
- `.mcp.json` server type becomes `stdio`.
- Distribution validator requires the harness, proxy/setup entry points, setup assets, and setup Skill.

- [ ] **Step 1: Replace old assertions with failing stdio contract tests**

Require exactly:

```python
self.assertEqual("stdio", server["type"])
self.assertEqual("python3", server["command"])
self.assertEqual(["scripts/processon_mcp_proxy.py"], server["args"])
self.assertEqual(".", server["cwd"])
self.assertNotIn("url", server)
self.assertNotIn("headers", server)
self.assertNotIn("env", server)
self.assertNotIn("env_http_headers", server)
```

Extend security tests to reject credential-like keys or literal authorization values anywhere in `.mcp.json` and to allow only the raw synthetic values defined inside tests.

- [ ] **Step 2: Run manifest/security tests and verify the direct HTTP config fails**

Run: `python3 -m unittest tests.test_manifest tests.test_security -v`

Expected: FAIL because `.mcp.json` still declares `type: http` and `env_http_headers`.

- [ ] **Step 3: Migrate `.mcp.json` and update the package validator**

Write the approved four-field stdio server declaration. Add all new runtime/setup files to `REQUIRED_FILES`, add `codex-processon-setup` to `SKILL_NAMES`, validate the exact stdio values, and reject direct header/env configuration. Preserve endpoint validation by checking `DEFAULT_ENDPOINT` in `processon_harness/mcp_proxy.py` through import-based tests instead of duplicating the URL in `.mcp.json` validation.

- [ ] **Step 4: Add and pass validator regression fixtures**

In `tests/test_distribution.py`, copy the package fixture to a temporary directory and prove validation reports errors for a missing setup asset, missing proxy entry point, altered stdio command, and a literal token-like MCP field. Each test must restore only its isolated fixture.

- [ ] **Step 5: Run focused distribution checks and commit**

Run:

```bash
python3 -m unittest tests.test_manifest tests.test_security tests.test_distribution -v
python3 scripts/validate_distribution.py
python3 /Users/wandl/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
git diff --check
```

Expected: all tests and both validators PASS.

Commit:

```bash
git add .mcp.json tests/test_manifest.py tests/test_security.py scripts/validate_distribution.py tests/test_distribution.py
git commit -m "feat: configure installed processon stdio proxy"
```

---

### Task 5: Credential Setup Skill and Router Handoff

**Files:**
- Create: `skills/codex-processon-setup/SKILL.md`
- Create: `skills/codex-processon-setup/references/workflow.md`
- Create: `skills/codex-processon-setup/references/security.md`
- Modify: `skills/codex-processon-use/SKILL.md`
- Modify: `skills/codex-processon-use/references/operations.md`
- Modify: `tests/test_skills.py`

**Interfaces:**
- Setup Skill invokes `python3 scripts/processon_setup.py check` and `python3 scripts/processon_setup.py ui` from the installed plugin root.
- Router recognizes `PROCESSON_SETUP_REQUIRED` and `PROCESSON_AUTH_REQUIRED` and delegates to `codex-processon-setup`.

- [ ] **Step 1: Read required Skill-authoring instructions before editing**

Read completely:

```text
/Users/wandl/.codex/skills/.system/skill-creator/SKILL.md
/Users/wandl/.agents/skills/skill-trace-checker/SKILL.md
```

Follow any directly referenced mandatory validation resources. Record the selected progressive-disclosure structure in the implementation commentary before changing Skill files.

- [ ] **Step 2: Write failing routing and safety tests**

Assert the new Skill has valid frontmatter and explicitly covers first use, missing credential, invalid credential, and token rotation. Assert the router names both stable error codes and routes them to `codex-processon-setup`. Assert no Skill asks the user to paste a token into chat, edit `.mcp.json`, write a shell profile, or print/check the token value.

- [ ] **Step 3: Run Skill tests and verify the missing Skill fails**

Run: `python3 -m unittest tests.test_skills -v`

Expected: FAIL because `skills/codex-processon-setup/SKILL.md` does not exist and the router still documents `PROCESSON_MCP_AUTHORIZATION`.

- [ ] **Step 4: Implement the setup Skill and router transition**

The Skill workflow must be sequential:

1. Run the safe availability check.
2. If missing or invalid, open the local setup UI.
3. Tell the user to paste the token only into the local password field.
4. Ask the user to reopen Codex after a successful save.
5. Verify through `initialize` and `tools/list` before any generation request.

Keep UI command details in `references/workflow.md` and security/rotation guidance in `references/security.md`. Replace the router's environment-variable-first instructions with stable error-code handoff. Keep `PROCESSON_MCP_TOKEN` only in advanced automation guidance.

- [ ] **Step 5: Run Skill validation and TRACE checks**

Run the exact validation commands prescribed by `skill-creator` and `skill-trace-checker`, plus:

```bash
python3 -m unittest tests.test_skills -v
python3 /Users/wandl/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
python3 scripts/validate_distribution.py
```

Expected: Skill tests, plugin validation, distribution validation, and TRACE checks PASS with no critical or high-severity finding.

- [ ] **Step 6: Commit the Skill workflow**

```bash
git add skills/codex-processon-setup skills/codex-processon-use/SKILL.md skills/codex-processon-use/references/operations.md tests/test_skills.py
git commit -m "feat: guide first-use processon authentication"
```

---

### Task 6: Bilingual Onboarding, Privacy, and Promo Integration

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `PRIVACY.md`
- Modify: `tests/test_docs.py`
- Preserve/Add: `assets/processon-hero.png`

**Interfaces:**
- Normal quick start: install → request a ProcessOn diagram → local three-step setup → reopen Codex → retry.
- Advanced automation: raw `PROCESSON_MCP_TOKEN` only.
- Generic MCP header example remains clearly labeled as a ProcessOn protocol reference, not the recommended Codex plugin configuration.

- [ ] **Step 1: Extend the existing uncommitted README tests before editing prose**

Build on, rather than replace, the current `tests/test_docs.py` changes. Require matching English/Chinese coverage for:

- hero image and official `ProcessOn` display name;
- automatic first-use setup;
- all three setup steps in the same order;
- platform credential paths and Unix modes;
- `PROCESSON_MCP_TOKEN` under advanced configuration only;
- no normal-user instruction to edit `.mcp.json` or shell profiles;
- HTTP 202 notification, one-time 401 refresh, and `UNKNOWN_WRITE_RESULT` semantics;
- official endpoint and generic inline-header reference;
- privacy disclosure that diagram prompts and authorization are sent to ProcessOn.

- [ ] **Step 2: Run documentation tests and verify current environment-first prose fails**

Run: `python3 -m unittest tests.test_docs -v`

Expected: at least one new first-use/setup parity assertion FAILS.

- [ ] **Step 3: Integrate the approved onboarding into both READMEs**

Preserve the existing hero asset and promotional positioning. Replace the normal environment export workflow with visual sequential onboarding. Put the generic JSON header example in an explicitly labeled interoperability section. Put raw-token environment override, setup CLI commands, and credential path override in advanced configuration. Document rotation as reopening the setup page and saving a new value; do not document credential deletion as an automatic operation.

- [ ] **Step 4: Update privacy disclosure and test-count evidence**

State that the user-level credential file is outside the plugin cache, the proxy reads it locally, and requests send the Authorization header plus user-provided diagram content to the official endpoint. After the full suite runs, update any README test-count badge or acceptance table to the measured final count; never predict the count.

- [ ] **Step 5: Run bilingual/document validation and commit the complete promo/docs unit**

Run:

```bash
python3 -m unittest tests.test_docs -v
python3 scripts/validate_distribution.py
python3 /Users/wandl/.agents/skills/full-stack-doc/scripts/validate_templates.py /Users/wandl/.agents/skills/full-stack-doc
git diff --check
```

Also run the exact README structural validator required by `full-stack-doc` if its current `SKILL.md` specifies a separate command.

Expected: documentation tests and validators PASS; English and Chinese structure and commands match.

Commit the already-approved promo and README work together with the authentication documentation:

```bash
git add README.md README.zh-CN.md PRIVACY.md tests/test_docs.py assets/processon-hero.png
git commit -m "docs: add friendly processon onboarding"
```

---

### Task 7: Integrated Regression, Security Audit, and Local Package Acceptance

**Files:**
- Modify as required by failing tests only: implementation and test files from Tasks 1–6
- Do not modify user-global credential state during synthetic acceptance

- [ ] **Step 1: Run the complete offline suite**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_distribution.py
python3 /Users/wandl/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
git diff --check
```

Record the exact test count and update README evidence only if needed. Re-run the suite after that edit.

- [ ] **Step 2: Run an isolated credential/setup acceptance**

Create a temporary directory with `mktemp -d`, set only `PROCESSON_CONFIG_PATH` for the child commands, and use a synthetic token. Exercise `check` before save, POST through the loopback fixture, `check` after save, file-mode checks, and token rotation. Remove the explicit temporary directory after confirming its resolved path is inside the system temporary location. Do not inspect or alter the user's default ProcessOn credential file.

- [ ] **Step 3: Run an offline proxy end-to-end fixture**

Launch the fixture server from `tests/test_processon_mcp_proxy.py` or a dedicated test helper. Pipe newline-delimited `initialize`, `notifications/initialized`, `tools/list`, and a synthetic `tools/call` into `scripts/processon_mcp_proxy.py` with the isolated config. Verify session propagation, empty 202 handling, one-line JSON-RPC framing, and no synthetic token in stdout/stderr.

- [ ] **Step 4: Scan the worktree, tracked content, and history for credentials**

Use the repository security test plus bounded Git scans for the known environment/config keys and bearer-pattern candidates. Review every match as either a documented identifier, a synthetic fixture, or a violation. Do not print matched secret values. Fail acceptance if any resolved token is found in source, untracked files, Git objects reachable from `main`, generated output, or logs.

- [ ] **Step 5: Review compatibility and failure behavior**

Manually verify:

- official plugin name/icons and marketplace entry remain unchanged;
- the stdio entry point resolves relative to installed plugin root;
- Python imports work from a directory outside the repository;
- missing credential yields setup-required JSON-RPC without process crash;
- invalid credential yields auth-required after one refresh;
- generation ambiguity yields `UNKNOWN_WRITE_RESULT` and zero automatic replay;
- existing prompt/review Skills and smoke diagnostics still pass.

- [ ] **Step 6: Perform completion review and commit only necessary fixes**

Use `superpowers:requesting-code-review` for the completed implementation review and `superpowers:verification-before-completion` before claiming completion. If review finds defects, add a failing regression test first, fix minimally, rerun all gates, and commit with a narrowly scoped message. Leave the branch local and ahead of `origin/main`; pushing and release/install acceptance require a separate user instruction.

---

### Task 8: Explicitly Authorized Live and Installed-Runtime Acceptance

**Precondition:** Execute this task only after the user explicitly asks to install/test the new build or publish it. Do not infer authorization from implementation approval.

**Files:**
- No source changes unless a live failure produces a reproducible failing regression test.

- [x] **Step 1: Build or resolve an immutable installation version**

Confirm local HEAD, tracking SHA, remote SHA if already pushed, and the exact cachebuster/version used by the Codex plugin installer. Treat commit, push, marketplace availability, installation, and runtime validation as separate evidence gates.

Executed 2026-09-14: local HEAD, `origin/main` ref, and the authoritative `git ls-remote` all returned `1a1681f`; the committed cachebuster was `0.1.0+codex.20260914044127`. Push was not performed, so the published revision predates the fix below.

- [x] **Step 2: Install from a clean cache and verify installed files**

Install the immutable GitHub revision through the supported Codex marketplace flow. Verify the installed `.mcp.json`, proxy/setup scripts, setup assets, setup Skill, display name, and official icons. Confirm the installed package contains no user credential file or token.

Executed 2026-09-14: `codex plugin remove` emptied the cache and `codex plugin add codex-processon-plugin@partme-ai-processon` reinstalled `0.1.0+codex.20260914044127`. The cache git HEAD equals `1a1681f`, all declared files are present, the display name is `ProcessOn` with the official icons, no credential file exists inside the package, and the resolved token appears in zero package files.

- [x] **Step 3: Complete the real first-use flow**

Have the user enter the ProcessOn Token only in the local password field. Do not copy it into chat, a shell command, test log, or source file. Reopen Codex and start a fresh task so MCP discovery uses the installed stdio configuration.

Executed 2026-09-14: the user-level credential file existed from the earlier local setup page, and `python3 scripts/processon_setup.py check` from the installed plugin root reported `ProcessOn credential: configured` without revealing any value. Fresh `codex exec` tasks were started from outside the repository.

- [x] **Step 4: Verify live protocol and one authorized generation call**

Run `initialize`, `notifications/initialized`, and `tools/list`, then make one explicitly authorized `generate_diagram_dsl` call with a harmless prompt. Confirm a valid accessible result without exposing authorization or raw response data that may contain sensitive content. Do not automatically repeat the generation call after an ambiguous failure.

Executed 2026-09-14. The first authorized call on the published revision was aborted at 30.1s and correctly surfaced `UNKNOWN_WRITE_RESULT` with zero retries; the same request completed in 12.0s and 27.3s when given a longer budget, which identified the 30s read timeout as the defect. The fix was committed locally as `94e3387` with a regression test whose mutation check reproduces the original error. On the fixed revision, `initialize` returned `2025-06-18` with serverInfo `streamable-mcp-server`, `tools/list` returned all three tools, and one authorized `generate_diagram_dsl` call completed with `isError: false` and a usable three-layer definition recorded in `artifacts/acceptance/credential-setup-stdio-dsl.json`.

Two of five otherwise successful `generate_diagram_dsl` calls returned a well-formed but empty payload (`isError: false`, empty text), including a 33.9s call that the old 30s timeout would have aborted. The proxy forwards that empty payload unchanged, so the user gets no artifact and no actionable error. This is recorded as `emptyPayloadFinding` in the acceptance summary and is deliberately **not** fixed here: the behaviour is upstream service variance rather than a reproducible defect, and mapping it to an error changes the plugin's response contract, which is a product decision.

- [x] **Step 5: Report proof levels separately**

Report local tests, local distribution validation, Git commit, remote push, clean installation, MCP discovery, read-only protocol success, and mutating generation success as distinct lines. If any gate is not performed, label it unverified rather than complete.

Executed 2026-09-14 in `artifacts/acceptance/acceptance-summary.json` under `proofLevels`: local tests, both validators, clean installation, MCP discovery, read-only protocol, and mutating generation are `VERIFIED`; remote push is `NOT_PERFORMED` because it needs separate authorization. Because the published revision still carries the defect, the verified build is installed locally through the personal marketplace (`codex-processon-plugin@personal`, `0.1.0+codex.20260914112340`); removing the older `codex-processon-plugin@partme-ai-processon` install was required because it kept owning the `processon` MCP name.

## Plan Self-Review Checklist

- [x] Every completion criterion in the approved spec maps to at least one task and executable verification step.
- [x] The plan contains no unresolved implementation placeholder, omitted branch, or conflicting credential source.
- [x] Public function names and constants are consistent across implementation and test steps.
- [x] Authentication refresh is the only automatic replay path.
- [x] User-global credential files were never read, overwritten, or deleted during synthetic tests.
- [x] Existing uncommitted promo/README work was preserved until its deliberate Task 6 commit.
- [x] Publication and installed-runtime proof remain gated behind explicit user authorization.
