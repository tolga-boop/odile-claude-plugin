# Odile Labs plugin for Claude Code

Two skills and one MCP server:

- **gate-setup**: put [Odile Gate](https://gate.odilelabs.com) in front of your API with curl. Each app or agent gets its own key, an allow-list of calls and a rate limit; a loop breaker stops an agent that keeps sending the same call; per-user rules keep signed-in users to their own rows. Free tier: 3 apps, 10,000 calls a month.
- **agent-phone-line**: give a business an AI receptionist, or let your agent message or book a business by its phone number, through the Odile MCP server (`https://odilelabs.com/mcp`).

[![Odile Gate in 58 seconds](https://img.youtube.com/vi/nv3lfb8Yleo/maxresdefault.jpg)](https://youtu.be/nv3lfb8Yleo)

Odile Gate in 58 seconds: [watch on YouTube](https://youtu.be/nv3lfb8Yleo).

## Install

```
/plugin marketplace add tolga-boop/odile-claude-plugin
/plugin install odile@odile-labs
```

Then ask Claude, for example: "put Odile Gate in front of my Supabase API so each user only reads their own orders".

## Notes

- Gate never stores request or response bodies; the upstream secret is encrypted (AES-GCM).
- A call that does not name the user cannot be checked per user; shape routes so the user id is in the path or query.
- Buying anything (Gate Pro, phone minutes) happens on Stripe's own checkout page, opened by you.

Made by [Odile Labs](https://odilelabs.com) (OdileUSA L.L.C.). Questions: hello@odilelabs.com. License: MIT.
