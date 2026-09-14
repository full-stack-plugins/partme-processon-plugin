# Privacy

Codex ProcessOn stores the current user's raw Token outside the plugin package at `$XDG_CONFIG_HOME/processon/credentials.json`, `~/.config/processon/credentials.json`, or `%APPDATA%\processon\credentials.json`. On Unix, the directory is restricted to `0700` and the file to `0600`. The committed repository and `.mcp.json` contain no resolved credential.

The local stdio proxy reads that credential and sends an `Authorization: Bearer` header, the diagram prompt, and any user-authorized remote attachment references only to ProcessOn's official MCP endpoint at `https://smart-hd.processon.com/mcp`. The process-level `PROCESSON_MCP_TOKEN` override is intended only for controlled automation.

Do not include secrets or unnecessary personal data in diagram prompts. The plugin does not upload local files automatically, manage ProcessOn accounts, or change cloud sharing permissions.

ProcessOn processes requests under its own terms and privacy practices. Review those practices before using confidential material.
