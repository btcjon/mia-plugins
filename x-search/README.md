# X Search: a Mia Bot plugin

Search X (Twitter) from Mia Bot with [xAI's X Search](https://docs.x.ai/developers/tools/x-search),
using **your own xAI API key**: what people say about a topic, what an account posted,
posts in a date range, and who is talking about something. Every post quoted comes with
its link. Read-only: it cannot post.

## Cost

Mia Bot charges nothing. xAI bills your own prepaid xAI credits (no free tier):
$5 per 1,000 posts fetched, $10 per 1,000 profiles fetched, plus model tokens. One search
usually costs about **$0.10 to $0.30**. Narrow searches cost less.

## Setup (once)

1. Sign in at https://console.x.ai.
2. Add credits (from $5) under **Billing**.
3. Create a key under **API Keys**.
4. In Mia Bot, open **Integrations**, find **X Search**, choose **Add**, then ask your bot
   to search X. It shows a secure card for the key. Paste the key there, never in chat.

The key is stored encrypted in your Vault and is sent only to `https://api.x.ai`. The bot
never sees it. Each search asks you to approve the request; choose **Always allow** to
stop the prompt. To remove the key, ask the bot to forget `xai_api_key`, or remove it in
**Settings → Vault**.

## Free fallback

To read one post, thread or profile from a pasted x.com link, the free `read-x` skill
needs no key. It cannot search.

## What is inside

- **Skill** `x-search`: sets up the key with `request_secret`, searches with
  `secret_request` to `POST https://api.x.ai/v1/responses` and the `x_search` tool
  (model `grok-4.3`, `max_turns` 2), and explains costs and errors.
- No MCP server and no code.

## Example prompts

- "Search X for what people say about electric bikes this week."
- "What did @nasa post about Artemis since November 1?"
- "Who on X is talking about our product launch? Leave out our own account @example."

## Notes

X and the X logo belong to X Corp. xAI and Grok belong to xAI. This plugin only tells
Mia Bot how to call xAI's public API with your key.
