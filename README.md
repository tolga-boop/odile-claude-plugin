# Odile Labs plugin for Claude Code

What it solves:

- **An agent with your API key can do anything that key allows.** It can repeat a call in a loop, read another customer's data, or change something nobody approved. Odile Gate gives each app its own key and a list of the calls it may make, stops a repeating agent, holds a risky write for a person to approve, and logs every call.
- **Your agent can't reach a business that has no API.** Odile Direct finds the business by its phone number and leaves it a message or books a time. 25 free sends per agent identity per UTC month, then $0.25 per delivered message or $1.00 per confirmed booking; $10 or $50 prepaid credit. Lookups and availability stay free; nothing renews.
- **Your app needs a phone line that answers.** The Odile MCP server gives it an AI receptionist line: free test line, then 25 cents a minute.

Three skills and two MCP servers:

- **gate-setup**: put [Odile Gate](https://gate.odilelabs.com) in front of your API with curl. Each app or agent gets its own key, an allow-list of calls and a rate limit; a loop breaker stops an agent that keeps sending the same call; per-user rules keep signed-in users to their own rows. Free tier: 3 apps, 10,000 calls a month.
- **odile-m2m**: reach a participating business by phone number; read its card, send a message, check availability or book the first open time with permission. MCP or dependency-free HTTPS helper; read task state and callback_check. Includes fictional demo guidance and phone fallback limits.
- **agent-phone-line**: give a business an AI receptionist, or let your agent message or book a business by its phone number, through the Odile MCP server (`https://odilelabs.com/mcp`).

[![Odile Gate in 60 seconds](https://img.youtube.com/vi/9wJtsjkIwoM/hqdefault.jpg)](https://youtu.be/9wJtsjkIwoM)

Odile Gate in 60 seconds: [watch on YouTube](https://youtu.be/9wJtsjkIwoM).

## Install

```
/plugin marketplace add tolga-boop/odile-claude-plugin
/plugin install odile@odile-labs
```

Then ask Claude, for example: "put Odile Gate in front of my Supabase API so each user only reads their own orders".

## Notes

- Gate does not put request or response bodies in its audit log. Approval-pending calls are stored encrypted; the upstream secret is encrypted (AES-GCM).
- A call that does not name the user cannot be checked per user; shape routes so the user id is in the path or query.
- Buying anything (Gate Pro, phone minutes) happens on Stripe's own checkout page, opened by you.

Made by [Odile Labs](https://odilelabs.com) (OdileUSA L.L.C.). Questions: hello@odilelabs.com. License: MIT.

The public read-only `get_agent_services` MCP tool explains when Gate enforcement or Direct business communication fits, how to connect and their limits. It reads no account and contacts no business. Gate’s `gate_check_setup` reports configuration gaps without upstream requests or policy changes; test backend ownership rules separately. Direct reaches participating businesses through the skills on their public cards. [Agent connection guide](https://odilelabs.com/a2a#connecting).

Gate admins can read `gate_metrics` for stored-call counts, measured duration including upstream wait and separate monthly usage, with partial audit coverage disclosed. Signed in with `direct:tasks` consent, `get_direct_usage` reads the caller’s allowance, prepaid Direct credits and last 20 charged tasks. It never buys credits or upgrades billing, and is outside the directory connector. The same usage appears at [Developers](https://odilelabs.com/developers#direct).

### Response redaction and merchant payment receipts

Response redaction on Free and Pro: choose an app’s JSON fields with gate_set_response, REST PUT /api/projects/<id>/apps/<app>/response, SDK admin.setResponse(app, allow), or its dashboard. JSON Pointer paths such as /id and /items/*/name keep only selected fields; selecting a container includes its subtree. Filtering is opt-in, capped at 1 MiB and a 5-second body read. Non-JSON, malformed or oversized replies are withheld; a withheld reply does not reverse a write. Response bodies are inspected only when filtering is enabled and are never stored.

Merchant payments (configured deposit pilot): the human approves Stripe Connect Checkout for the business’s configured service deposit. get_direct_payment, with direct:tasks consent, reconciles the caller’s existing task and returns Stripe-verified payment evidence, a receipt when available and separate booking state. It creates no new charge identity; a paid hold may finish its authorized booking. Bank payout status is unknown. Availability requires an enabled pilot, a connected merchant and provider configuration; no payment without human checkout.

Runnable Direct examples (curl, Python, TypeScript, MCP SDK, LangChain, CrewAI, Vercel AI SDK, OpenAI Agents SDK): [tolga-boop/odile-m2m-examples](https://github.com/tolga-boop/odile-m2m-examples). The new `odile-m2m` skill is also packaged for Claude.ai Skills upload. Uploading a skill does not connect MCP; add `https://odilelabs.com/mcp` separately. [Live Direct capabilities and prices](https://odilelabs.com/a2a) are authoritative.

## gitagent

The same plugin installs into a [gitagent](https://github.com/open-gitagent/gitagent) agent (the manifest is `plugin.yaml`; `skills/` points at the same three skills):

```sh
gitagent plugin install https://github.com/tolga-boop/odile-claude-plugin.git
```

Then add the two hosted MCP servers to `agent.yaml` so the skills have their tools:

```yaml
mcp_servers:
  odile:
    type: http
    url: "https://odilelabs.com/mcp"
  gate:
    type: http
    url: "https://gate.odilelabs.com/mcp"
```

Both servers answer their public tools (prices, the receptionist benchmark, Gate's setup check) before any sign-in; the rest asks you to sign in once in a browser.
