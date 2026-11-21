# Composio: a Mia Bot plugin

Connect Mia Bot to [Composio](https://composio.dev) and reach Gmail, Google Calendar,
Outlook, Slack, Notion, GitHub and 1,500+ other apps through one hosted MCP server.

## Installation

In Mia Bot, open **Integrations**, find **Composio**, and click **Add**.

On first connection, Mia Bot opens the Composio sign-in in your browser. Sign in with your
Composio account. No API key is needed and nothing should be pasted into chat. When the
bot first needs an app (for example Gmail), Composio gives a link to approve that app.

## What you get

- **MCP server** `composio` at `https://connect.composio.dev/mcp` (Streamable HTTP, OAuth 2.1).
- **Skill** `composio`: how to use Composio well (search before running, read the schema,
  connect apps on demand, confirm before sending or changing anything, batch independent reads).

### Tools

Composio Connect exposes 7 meta-tools:

| Tool | What it does |
|---|---|
| `COMPOSIO_SEARCH_TOOLS` | Find the tools for a request, with a suggested plan |
| `COMPOSIO_GET_TOOL_SCHEMAS` | Input schemas for the tools found |
| `COMPOSIO_MULTI_EXECUTE_TOOL` | Run up to 50 tools in parallel |
| `COMPOSIO_MANAGE_CONNECTIONS` | Create, list, rename or remove app connections |
| `COMPOSIO_WAIT_FOR_CONNECTIONS` | Wait for the user to finish an app sign-in |
| `COMPOSIO_REMOTE_WORKBENCH` | Run Python in a remote sandbox |
| `COMPOSIO_REMOTE_BASH_TOOL` | Run bash in a remote sandbox |

## Example prompts

- "What's on my calendar today, and which 3 emails need a reply?"
- "Connect my Slack."
- "Which apps do I have connected?"

## Notes

The Composio name and logo belong to Composio. This plugin only points Mia Bot at Composio's
public hosted server; see https://docs.composio.dev/docs/composio-connect.
