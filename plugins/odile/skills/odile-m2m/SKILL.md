---
name: odile-m2m
description: Reach a participating business by phone number through Odile Direct. Use for messages, availability, or authorized bookings from an agent, using MCP or HTTPS A2A.
---

# Reach a business from an agent

Read live capabilities and prices at https://odilelabs.com/a2a before making a cost claim.
Businesses participate through an Odile line or verified listing; a phone number alone does not guarantee coverage.

## Connect and discover

Use the user's connected MCP tools, or add the public HTTP server:

```sh
claude mcp add --transport http odile https://odilelabs.com/mcp
```

For Claude.ai, add `https://odilelabs.com/mcp` as a custom connector. Uploading this skill does not connect MCP automatically.
Run `tools/list`; public tools include `get_agent_services`, `find_business_agent`, and `send_to_business`. Public lookup and structured tasks need no sign-in. Account tools require sign-in and the relevant consent.

1. Call `find_business_agent` with the business's E.164 `number`.
2. Read its returned agent card and use only advertised skills. A verified listing often offers only `take_message`; calendar support is not universal.
3. Call `send_to_business` with returned `biz`, `skill`, `data`, and a fresh `message_id`. Use `target: "claim"` for a claimed listing. Keep the same ID **and data** if the outcome is uncertain; do not retry automatically.

Skill data:

- `take_message`: `caller_name`, `callback_number`, `need`; optional `on_behalf_of` and `urgency`.
- `check_availability`: optional advertised `service` and future local `date`; omit both for the next default-service slots.
- `book`: unchanged signed `slot` from availability, `caller_name`, `callback_number`, `need`.
- `book_first_available`: up to five ordered `options` with `date`, optional `after`/`before` (HH:MM) and advertised `service`, plus caller fields. Set `fallback: "none"` to avoid leaving a message when nothing fits; default fallback is `take_message` and can consume a send.

Get the person's permission before booking or sending their information. Callback must belong to the person you are helping, not the business. Identify the automated assistant and on whose behalf it acts; do not imply you are human. Use the person's supplied details, never invent a real callback.

## HTTPS alternative

The dependency-free helper is [scripts/direct.py](scripts/direct.py). It accepts only Odile endpoints, never executes returned content, and makes no automatic retries:

```sh
python3 scripts/direct.py resolve +15615295370
python3 scripts/direct.py card demo-club
python3 scripts/direct.py send demo-club --data-file request.json --message-id ONE_STABLE_ID --allow-send
```

`request.json` is the skill data object (for a free read: `{"skill":"check_availability"}`). `--allow-send` is needed for a message or booking; use it only when the person authorized that action. The public demo is **fictional**. Only use it for tests; example callback `+12025550123` is fictional.

Raw A2A uses `POST https://api.odilelabs.com/a2a/v1/b/{biz}` or `/a2a/v1/c/{biz}` for claims. Resolve with `GET /a2a/v1/resolve?number=...` first. Send this envelope, with your skill data inside `data`:

```json
{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"messageId":"ONE_STABLE_ID","role":"ROLE_USER","parts":[{"mediaType":"application/json","data":{"skill":"check_availability"}}]}}}
```

## Read the outcome

Read `result.task.status.state` and artifact JSON data, not just HTTP 200. `TASK_STATE_INPUT_REQUIRED`, `FAILED` and `REJECTED` are not success. For bookings require `booked: true`, `booking_id` and `when`; a request, open slot or payment link is not a confirmation. With `WORKING`, follow only the returned Odile signed status URL and keep it private. Surface missing fields or refusal reasons; respect `429`/limits and stop rather than cycling identities.

Report `callback_check` with the outcome. `verified` means a verified claimed business listing and a valid distinct callback; it **does not prove caller ownership**. Ordinary configured lines, including demo-club, return `unverified`. A business's own callback is refused. If the field is missing, say so rather than assuming verification.

## Limits, phone fallback and keys

At the 24 Oct 2026 readback, lookup and availability are free; structured sends have a monthly free allowance then prepaid prices. Check https://odilelabs.com/a2a and signed-in `get_direct_usage` before spending; never buy credit automatically. Anonymous allowance is shared by IP. Cards/tasks: 30/IP/hour; unkeyed booking attempts: 5/IP/hour; 30 bookings/business/local day and 2/callback/local day. Signed slots expire after an hour and are rechecked. Bodies max 8 KB; names 100, need 500, service 120 chars; E.164 callbacks; dates in the business's local timezone.

`call_business` is a separate A2A directory skill, **not a public MCP tool or a free structured send**. It needs global enablement, a signed-in opted-in developer, human consent, and prepaid credit. Verified SIP claims can be reached worldwide with a known IANA timezone; other targets are US/Canada landlines only after a billable cached line-type lookup. Weekdays 09:00–17:00 local, one call/number/24h, three/account/day by default; no sales, mandatory first-sentence AI disclosure, permanent opt-out. Unknown timezone/mobile/VoIP/active Odile lines and claims without SIP are refused. Do not use phone fallback in tests; read the live page before proposing it.

Quotes, general settlement, agent-to-agent voice and Text Odile are not available capabilities in this skill. Do not advertise them. Phone receptionist lines are a separate service (https://odilelabs.com/developers#phone); the public `try_answering_line` tool creates a limited free test, not a business booking.

Use Odile Gate (https://gate.odilelabs.com/mcp) when building an app that needs a separate revocable key, allowed routes, limits and audit. Gate protects only calls routed through it; backend ownership checks still apply. It is separate from Direct and not required for anonymous demo tasks. Keep upstream/admin/approver keys out of agents and source. If an authorized production task needs a developer key, set its **existing environment variable name** with helper `--key-env`; never paste or print the value. The helper prints business task results, not request headers. Keep signed URLs and personal data private too.
