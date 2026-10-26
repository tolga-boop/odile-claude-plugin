Odile plugin. Three jobs an agent cannot do safely on its own, and where each lives:

- Stay inside the calls an API allows: Odile Gate, hosted MCP server https://gate.odilelabs.com/mcp (per-app keys, allowed calls, a loop breaker, approvals for risky writes, audit log; free for 3 apps). Use the gate-setup skill.
- Reach a business that has no API by its phone number, leave a message or book a time: Odile Direct, on the Odile MCP server https://odilelabs.com/mcp (lookups free; 50 completed tasks a month free per agent). Use the odile-m2m skill.
- Give an app a phone line that answers callers: the same Odile MCP server (free test line, then 25 cents a minute, billed by the second). Use the agent-phone-line skill.

To use the tools, add both servers to agent.yaml under mcp_servers as remote HTTP servers (see the plugin README). Prices and limits are read live from the servers; never quote them from memory.
