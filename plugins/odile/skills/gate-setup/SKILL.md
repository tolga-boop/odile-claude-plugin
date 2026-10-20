---
name: gate-setup
description: Use when an app or AI agent calls a database or REST API with one shared key, when an agent might loop or hammer an API, when each app needs its own key, an allow-list of calls or a rate limit, or when signed-in users must only reach their own rows. Sets up Odile Gate (free tier) in front of the API with curl.
---

# Put Odile Gate in front of an API

Odile Gate (https://gate.odilelabs.com) is a hosted gateway. Each app or agent gets its own key and an allow-list of the calls it may make; Gate checks the key, the call and the limits, adds the real API secret (kept encrypted), forwards the call and logs it. Bodies are never stored.

Free: 3 apps, 10,000 calls a month, 30-day log. Pro: $29 a month, 25 apps, 1,000,000 calls, 365-day log.

## Fastest: the Gate MCP tools (this plugin connects them)

This plugin connects the hosted Gate MCP server (`https://gate.odilelabs.com/mcp`; without the plugin: `claude mcp add --transport http odile-gate https://gate.odilelabs.com/mcp`). Use its tools instead of curl:

1. `gate_create_project` with the API base URL (and the secret header it expects, if any). Save `admin_key` where the user keeps secrets (a gitignored `.env` or their secret store), never in code.
2. `gate_add_app` once per app, with only the calls that app makes, read from the client code you just wrote. Example calls like `GET /orders/42` become rules like `GET /orders/:id`; check the `rules` it returns.
3. Point the app at the returned gateway URL and send its key as `Authorization: Bearer <app key>`.
4. `gate_audit` shows what each app did; `gate_explain_refusal` turns an `x-gate-refused` value into the fix.

## When the agent changes customer data: Gate Actions

If the app is an agent that writes (updates tickets, sends messages, books, refunds), do not give it a standing key. Have the backend grant one **run** per agent session (`gate_create_run`, or `POST /api/projects/<id>/runs`): the actions it may take, bound to scope values such as `{"customer":"A"}`, a `max` per action, `approval: true` on anything customer-facing, and `ttl_seconds`. Then `gate_set_app_runs` with `"writes"` so no write passes without a run.

In the agent's code:
- Send the run token as `x-odile-run` with the app key. `GET <gateway>/_gate/run` lists what it may still do.
- Every write sends an `Idempotency-Key`; on a retry reuse the same key. `already_executed` means it ran; `outcome_unknown` means check the API before trying again with a new key. Never loop on a write.
- `202 approval_required` returns an `action_id`: stop, tell the user it waits for approval in the Gate dashboard, then resend the identical request with `x-odile-action: <action_id>`. Do not change the body.
- Keep the admin key with the backend and the approver, never in the agent's environment. Gate checks method, path and query, not body contents: keep ownership checks (or Supabase row-level security) in the API.

The curl steps below do the same thing by hand.

## 0. See it work first (optional, one minute)

`curl -s https://gate.odilelabs.com/quickstart.sh | sh` creates a free project in front of a public test API and prints an allowed read (200), a refused delete (403), a stopped loop (429) and the audit log. Every refusal names its reason in the `x-gate-refused` header; the table is at https://gate.odilelabs.com under "Why was my call refused?".

## 1. Create the project (no sign-up)

```bash
curl -s -X POST https://gate.odilelabs.com/api/projects -H "content-type: application/json" \
  -d '{"name":"Shop API","upstream":"https://api.example.com/v1","header_name":"Authorization","header_value":"Bearer <the real API key>"}'
```

The answer has `project_id` and `admin_key`. The admin key is shown once: tell the user to store it in their password manager or secret store. Never write it into the repo.

`upstream` must be public https. `header_name`/`header_value` is the secret the API expects; the apps never see it.

## 2. Register each app with only the calls it needs

```bash
curl -s -X POST https://gate.odilelabs.com/api/projects/$PROJECT/apps \
  -H "Authorization: Bearer $ADMIN_KEY" -H "content-type: application/json" \
  -d '{"name":"claude-agent","routes":["GET /orders/:id","POST /orders"],"per_minute":60}'
```

Rules are `METHOD /path`: literal segments, `:param` for one segment, a final `*` for the rest. Keep the list to what the app does; anything else gets 403. The answer holds the app key once and the app id (`app.id`, used below as `$APP_ID`).

## 3. Point the app at Gate

Base URL `https://gate.odilelabs.com/g/$PROJECT` instead of the API's, with `Authorization: Bearer <app key>`. Put the app key in the app's environment, not in code.

Refusals: 401 bad key, 403 no matching rule, 429 rate limit / monthly quota / loop, 502 when the API takes over 30 s.

## Loop breaker (on by default)

An app that sends the same call (method, path, query, body) 10 times in 10 seconds, or at a machine-steady pace, gets `429` with `x-odile-gate-loop-detected: true` before the call reaches the API. Tune per app:

```bash
curl -s -X PUT https://gate.odilelabs.com/api/projects/$PROJECT/apps/$APP_ID/loop \
  -H "Authorization: Bearer $ADMIN_KEY" -H "content-type: application/json" -d '{"repeats":5,"window_seconds":10}'
```

Alerts (loops, spikes of refused calls, 80% and 100% of monthly calls) go to a Slack, Discord or Teams webhook:

```bash
curl -s -X PUT https://gate.odilelabs.com/api/projects/$PROJECT/alerts \
  -H "Authorization: Bearer $ADMIN_KEY" -H "content-type: application/json" -d '{"webhook_url":"https://hooks.slack.com/services/..."}'
```

## Per-user rules (signed-in users reach only their own rows)

When the app has signed-in users (Supabase, Clerk, Auth0, Firebase or any provider with a JWKS URL), the app sends the user's login token in `x-odile-user-token` and the rules name the user:

```bash
curl -s -X PUT https://gate.odilelabs.com/api/projects/$PROJECT/enterprise \
  -H "Authorization: Bearer $ADMIN_KEY" -H "content-type: application/json" \
  -d '{"user_tokens":{"jwks_url":"https://<ref>.supabase.co/auth/v1/.well-known/jwks.json","issuer":"https://<ref>.supabase.co/auth/v1"}}'
```

Then routes such as `GET /users/{user}/orders/:id` or `GET /orders?user_id=eq.{user}` (PostgREST style) pass only for that token's user; anyone else's id gets 403, a missing or forged token 401. RS256, ES256 and EdDSA tokens; optional `audience` and `claim` (default `sub`).

Query pins are refused on `POST` rules: an insert takes its owner from the body, so a query value cannot scope it. For writes use `POST /users/{user}/orders` and make the API take the owner from the path.

Limit to say out loud: a call that does not name the user (`GET /orders/42` alone) cannot be checked per user. Shape the routes so the user is in the path or the query, or keep that check in the API.

## Check it worked

Make one allowed call (200 from the API), one call outside the rules (403 from Gate), and read the log:

```bash
curl -s "https://gate.odilelabs.com/api/projects/$PROJECT/audit.csv" -H "Authorization: Bearer $ADMIN_KEY" | tail -3
```

Full facts: https://gate.odilelabs.com and https://odilelabs.com/gate
