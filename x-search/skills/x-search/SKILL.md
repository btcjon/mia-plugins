---
name: x-search
description: >-
  Search X (Twitter) with xAI's X Search, using the user's own xAI API key: what people
  are saying about a topic, what an account posted, posts in a date range, and who is
  talking about something. Keyword and meaning-based search with links to every post
  quoted. Use when the user asks to search X or Twitter, asks what people say on X, or
  wants recent posts from an account. For one x.com link the user pasted, read-x is
  free and needs no key.
---

# X Search (your own xAI key)

This skill searches X through xAI's Responses API with its `x_search` tool. The request
runs on the user's own xAI account and key. Mia Bot charges nothing for it and never
sees the key: the key sits in the user's Vault and the backend adds it to the request.

## What it costs the user (say this before the first search)

- xAI bills the user's own prepaid xAI credits. There is no free tier.
- One search usually costs **about $0.10 to $0.30**: $5 per 1,000 posts fetched and
  $10 per 1,000 profiles fetched, plus model tokens. Narrow searches (one account, a
  short date range) cost less.
- To start: sign in at https://console.x.ai, add credits (from $5) under Billing, and
  create an API key under API Keys. Then paste the key into the secure card that Mia Bot
  shows, never into chat.
- Each search asks the user to approve the request to api.x.ai. They can choose
  "Always allow" to stop the prompt.

## Free fallback: read-x

When the user has no xAI key, does not want one, or only pasted a single
`x.com/<handle>/status/<id>` link, a profile or wants trends, use the `read-x` skill if
it is installed. It is free and needs no key, but it reads one post, thread or profile
at a time and **cannot search**. Do not use web search to pretend to search X.

## 1. Set up the key (first time only)

Call `list_secrets`. If it shows `xai_api_key`, go to step 2.

Otherwise, give the user the three-line cost note above, then call `request_secret`:

```json
{
  "label": "xAI API key",
  "purpose": "api_key",
  "credential": {
    "name": "xai_api_key",
    "origin": "https://api.x.ai",
    "auth": { "type": "bearer" }
  }
}
```

Never ask for the key in chat. If the user pastes a key in chat anyway, tell them to
delete that message, revoke the key at https://console.x.ai, and use the card with a new
key.

## 2. Search

Call `secret_request`. `body` is a JSON string:

```json
{
  "name": "xai_api_key",
  "url": "https://api.x.ai/v1/responses",
  "method": "POST",
  "contentType": "application/json",
  "body": "{\"model\":\"grok-4.3\",\"max_turns\":2,\"input\":\"Search X for: what people say about electric bikes this week. Answer in at most 250 words. For each post you rely on, give the author handle, the date, a short exact quote and its https://x.com/<handle>/status/<id> link.\",\"tools\":[{\"type\":\"x_search\",\"from_date\":\"2026-11-14\"}]}"
}
```

Build the body like this:

- `model`: `grok-4.3` (lowest cost). If xAI answers that the model does not exist or does
  not support the tool, use `grok-4.7` once and tell the user it costs more per token.
- `max_turns`: `2`. Keep it at 1 or 2: the request must finish within 30 seconds and
  more turns fetch more paid posts.
- `input`: the user's request in plain words, plus the answer instructions in the
  example (word limit, handle, date, exact quote, post link). The reply is cut at
  20,000 characters, so always ask for a short answer.
- `tools`: exactly one entry, `{"type":"x_search"}`, with only the filters the user asked
  for:
  - `allowed_x_handles`: only these accounts. Up to 20 handles, without `@`.
  - `excluded_x_handles`: leave these accounts out. Up to 20, without `@`. Never send
    it together with `allowed_x_handles`.
  - `from_date` / `to_date`: `YYYY-MM-DD`, UTC. `from_date` is included, `to_date` is
    not: for one day, set `to_date` to the next day. Use the user's time zone to work
    out the dates.
  - `enable_image_understanding` / `enable_video_understanding`: `true` only when the
    user asks about images or videos in posts. They add cost.

## 3. Read the answer

The response is JSON. The answer text is in `output[]` items with `type: "message"`,
then `content[]` items with `type: "output_text"`, field `text`. Links to the posts are
in that block's `annotations[]` (`type: "url_citation"`, field `url`) and inline in the
text. Usage is in `usage.server_side_tool_usage_details` (`x_posts_fetched`,
`x_users_fetched`).

Tell the user what was found, with each post's link. Quote post text exactly; never
invent a post, handle, date or link. If the user asks what a search cost, estimate it
from `x_posts_fetched` × $0.005 + `x_users_fetched` × $0.01, plus a few cents of tokens.

## When something fails

Never retry a failed search in a loop. At most one retry, and only after a timeout.

- **401 or "invalid API key"**: the key is wrong or revoked. Offer a new card:
  `request_secret` with the same body and `"replace": true`.
- **402, 403 with a credits or spending-limit message**: the xAI account has no credits
  left or hit its limit. Tell the user to add credits or raise the limit at
  https://console.x.ai (Billing).
- **429**: xAI rate limit. Tell the user to try again in a minute.
- **Timeout**: retry once with `max_turns` 1 and a narrower request (one account or a
  shorter date range).
- **The user wants to remove the key**: call `forget_secret` with
  `{"name":"xai_api_key"}` and tell them they can also revoke it at https://console.x.ai.

## Limits

- Read-only: this skill cannot post, reply, like, follow or send messages.
- Public posts only. Protected accounts and private messages are not searchable.
