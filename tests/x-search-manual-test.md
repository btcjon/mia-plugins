# x-search: manual test with a real xAI key

Needs: a Mia instance with the x-search card installed (staging first), and an xAI API key
with a few dollars of credit (https://console.x.ai → Billing, then API Keys). Expected spend
for the whole plan: under $2.

1. **Install.** Integrations → find X Search (or + → From GitHub →
   `https://github.com/btcjon/mia-plugins/tree/<sha>/x-search` → Preview). Expect 1 skill,
   0 servers, nothing skipped. Choose Add.
2. **Key card.** In a bot chat: "Search X for what people say about electric bikes this week."
   Expect: a short cost note ($0.10 to $0.30 per search, link to console.x.ai), then a
   protected card titled xAI API key showing `https://api.x.ai`. The bot does not ask for the
   key in chat. Paste the key in the card.
3. **First search.** Expect an approval card for a request to api.x.ai (choose Allow once).
   Expect a short answer with handles, dates, exact quotes and working
   `https://x.com/<handle>/status/<id>` links. Open 2 links and check the quotes match.
   Note the time taken (must be under 30 s) and whether `grok-4.3` worked (if the bot switched
   to `grok-4.7`, note it).
4. **Filters.** "What did @nasa post since November 1?" Expect `allowed_x_handles: ["nasa"]`
   (no @) and `from_date` in the request shown on the approval card; results only from @nasa.
5. **Reuse.** New chat, another search. Expect no new key card (`list_secrets` finds
   `xai_api_key`).
6. **Cost.** "What did that search cost?" Expect an estimate from `x_posts_fetched`. Compare
   with console.x.ai → Usage after a few minutes.
7. **Fallback.** Paste one x.com post link and ask what it says. Expect read-x (free, no
   api.x.ai request) if installed.
8. **Bad key.** Settings → Vault → edit `xai_api_key` to a wrong value, search again. Expect
   one 401 and an offer of a new card (`replace: true`), no retry loop. Put the real key back.
9. **Forget.** "Forget my xAI key." Expect `forget_secret` and a note to revoke it at
   console.x.ai. Check Settings → Vault no longer lists it.
10. **Leak check.** Search the chat transcript and the run's tool results for the first 8
    characters of the key: expect no match.
