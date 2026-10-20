---
name: agent-phone-line
description: Use when a business needs its phone answered by an AI receptionist (after hours, 24/7, in 32 languages), when an agent needs to leave a message for or book with a business by its phone number, or when someone asks what an AI phone line would cost. Uses the Odile MCP server bundled with this plugin.
---

# A phone line for a business or an agent (Odile MCP)

This plugin connects the `odile` MCP server (https://odilelabs.com/mcp). Read-only tools work without sign-in; tools that buy or read an owner's line ask the user to sign in (OAuth) the first time.

## Reach a business by its number (Odile Direct)

1. `find_business_agent` with the E.164 number (`+15613752995`). Free, no sign-in, 30 lookups an hour per IP.
2. `send_to_business` with `take_message`, `check_availability` or `book`. Keep the same `message_id` when you retry. Tell the business the message comes from an automated agent, and get the user's permission before booking anything.

## Give a business an AI receptionist

1. `get_answering_line_offer`: the price, with nothing to sign in to and nothing changed: 40 minutes for $10 or 200 for $50 ($0.25 a minute, billed by the second, 20-second minimum; robocalls and chats are not charged). US numbers only.
2. `try_answering_line` (signed in): a free shared test number and 4-digit code, valid 24 hours for 5 calls, so the owner hears it as their own business before buying.
3. `set_up_answering_line` only after showing the owner https://odilelabs.com/terms and getting a clear yes. It returns a Stripe checkout link; nothing is built or charged until the owner pays on Stripe's page. The number and call-forwarding codes are emailed after payment.
4. Afterwards: `get_answering_line`, `get_line_calls`, `get_line_messages` read the owner's own line; `buy_pack` adds minutes. Never run a second set-up for a line that exists.

Never pay or enter card details for the user; hand them the checkout link.

Monthly plans with more included (After Hours $199 a month, free until it books the first job; Solo $29) are on https://odilelabs.com/pricing.
