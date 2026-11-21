# Mia Bot plugins

Mia Bot plugins: apps for the Mia Bot app catalog. Each folder is one plugin in the same layout as the
[xAI plugin marketplace](https://github.com/xai-org/plugin-marketplace): a manifest in
`.grok-plugin/plugin.json`, a hosted MCP server in `.mcp.json`, a logo in `assets/`, and
skills in `skills/<name>/SKILL.md`.

| Plugin | What it does |
|---|---|
| [composio](composio) | Gmail, Google Calendar, Outlook, Slack and 1,500+ apps through Composio Connect |
| [x-search](x-search) | Search X with xAI's X Search, using your own xAI API key (skills only) |

App names and logos belong to their owners.

## App cards (via Composio)

Skills-only cards for common apps: Gmail, Google Calendar, Google Drive, Google Docs, Google Sheets, Outlook, OneDrive, Teams, Slack, HubSpot, Salesforce, Zoom, GitHub, X and Asana. Each adds one short skill that uses the user's own Composio connection for that app's toolkit. They have no server of their own and need the `composio` plugin, connected.
