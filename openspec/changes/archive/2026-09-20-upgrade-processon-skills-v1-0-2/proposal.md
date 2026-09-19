## Why

`processon-skills v1.0.2` removes the obsolete Codex-only consumer identity and passed the package quality gates, but automated dispatch is blocked because the source workflow cannot see `SKILLS_SYNC_TOKEN`.

## What Changes

- Manually re-pin the managed ProcessOn skill source to immutable `v1.0.2` and its peeled SHA.
- Verify the vendored snapshot online and offline.

## Capabilities

### New Capabilities

- `processon-skill-source`: Defines the exact immutable ProcessOn skill source consumed by the plugin.
