---
name: composio
description: >-
  Work with the user's other apps through Composio Connect: Gmail, Google Calendar,
  Outlook, Slack, Notion, GitHub, HubSpot, Linear and 1,500+ more. Search for the right
  app action, connect an app the first time it is needed, and run actions across apps,
  in parallel when they are independent. Use whenever the user asks about their email,
  calendar, messages, documents, tasks or any other app that has no dedicated
  integration here, or says "Composio".
---

# Composio

Composio Connect is one hosted MCP server that reaches 1,500+ apps. The `composio` MCP
server bundled with this plugin acts as the signed-in Composio user. Each app the user
connects through it (Gmail, Google Calendar, Slack and so on) is the user's own account,
authorized by the user in their browser.

The server does not list every app tool. It exposes 7 meta-tools: you search for the
tool you need, read its schema, then run it.

## Before you act

0. **Connect apps through Composio.** For any app connection (Gmail, Google Calendar,
   Outlook, Slack and the rest), use the Composio tools below, not the built-in
   connector catalog (`connect_app`).
1. **Search, do not guess.** Call `COMPOSIO_SEARCH_TOOLS` with the user's request in
   plain words. Use only the tool slugs it returns. Never invent a slug, an ID, an email
   address or a time zone.
2. **Read the schema first.** Call `COMPOSIO_GET_TOOL_SCHEMAS` for the slugs you plan to
   run, and fill the inputs from it.
3. **Connect apps on demand.** When search shows the app is not connected, call
   `COMPOSIO_MANAGE_CONNECTIONS` to create the connection and give the user the link it
   returns, as a link, with one sentence on what it is for. Then call
   `COMPOSIO_WAIT_FOR_CONNECTIONS` and continue when the user has approved. Links are
   short-lived; if one expires, make a new one.
4. **Confirm before you change or send anything.** Sending email or messages, creating,
   moving or cancelling events, deleting anything, and posting to other people need an
   explicit yes from the user first. Reading and searching do not.
5. **Times.** Ask for, or look up, the user's time zone before you work with times.
   Show results in that time zone.

## Choosing a tool

| You want to | Use |
|---|---|
| Find the right action for a request | `COMPOSIO_SEARCH_TOOLS` (returns tool slugs and a suggested plan) |
| See a tool's inputs | `COMPOSIO_GET_TOOL_SCHEMAS` |
| Run one or more actions | `COMPOSIO_MULTI_EXECUTE_TOOL` (up to 50 per call; independent actions run in parallel) |
| See, add, rename or remove app connections | `COMPOSIO_MANAGE_CONNECTIONS` |
| Wait for the user to finish an app sign-in | `COMPOSIO_WAIT_FOR_CONNECTIONS` |
| Process a large result or many items in bulk | `COMPOSIO_REMOTE_WORKBENCH` (Python) or `COMPOSIO_REMOTE_BASH_TOOL` (bash) in Composio's remote sandbox |

Batch independent reads in one `COMPOSIO_MULTI_EXECUTE_TOOL` call, for example today's
calendar events and the unread email list together.

## Common requests

- **"What's on my calendar today?"** Search for the calendar list-events action, run it
  for today in the user's time zone, and summarize by time.
- **"Which emails need a reply?"** Search for the email fetch action, read recent unread
  messages, and list the few that ask the user for something, with sender and subject.
- **"Connect my Slack" (or any app).** Use `COMPOSIO_MANAGE_CONNECTIONS` and send the
  link it returns.
- **"What apps are connected?"** List the connections with `COMPOSIO_MANAGE_CONNECTIONS`.

## When something fails

- **Auth error on an app.** List the connection; if it is unhealthy, offer a fresh
  connection link and retry after the user approves.
- **No suitable tool found.** Tell the user plainly that Composio does not support that
  action yet. Do not try an unrelated tool instead.
- **Usage limit.** Composio's free plan has a monthly limit on tool calls. If Composio
  reports a limit, tell the user; do not retry in a loop.

## More

- Composio Connect docs: https://docs.composio.dev/docs/composio-connect
- Manage connected apps and usage in the Composio dashboard: https://dashboard.composio.dev
