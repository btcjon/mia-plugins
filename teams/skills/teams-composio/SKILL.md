---
name: teams-composio
description: >-
  Use the user's Teams through their Composio connection: read and send chat and channel messages, and find meetings. Use when the user
  asks about Teams or wants to connect it.
---

# Teams via Composio

This card works through the user's Composio app (the `composio` MCP server). Teams is
the Composio toolkit `microsoft_teams`; its tools start with `MICROSOFT_TEAMS_`.

1. **Use Composio, not the built-in connector catalog.** Do not call `connect_app` for
   Teams. If no Composio tools (`COMPOSIO_SEARCH_TOOLS` and the others) are available,
   tell the user to open Integrations, add Composio and sign in, then ask again.
2. **Connect on first use.** Call `COMPOSIO_MANAGE_CONNECTIONS` for the toolkit
   `microsoft_teams`. If it returns a link, give it to the user as a link with one sentence on
   what it is for, then call `COMPOSIO_WAIT_FOR_CONNECTIONS` and continue once approved.
   Links are short-lived; make a new one if it expires.
3. **Search, do not guess.** Call `COMPOSIO_SEARCH_TOOLS` with the request in plain
   words, and use only `MICROSOFT_TEAMS_` tool slugs it returns. Read them with
   `COMPOSIO_GET_TOOL_SCHEMAS`, then run them with `COMPOSIO_MULTI_EXECUTE_TOOL`.
   Never invent an ID, address or time zone.
4. **Confirm before changes.** Sending, posting, creating, editing, moving, sharing or
   deleting anything needs the user's explicit yes first. Reading and searching do not.
5. **Times.** Use the user's time zone; ask or look it up before working with times.
