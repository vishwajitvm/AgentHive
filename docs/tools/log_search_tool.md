# Log Search Tool ($(@{name=Log Search Tool; slug=log_search_tool; description=Searches agent/tool/workflow logs.; category=system; input_schema=; output_schema=; requires_auth=False; required_env_keys=System.Object[]; safe_mock_mode=False}.slug))

## 📖 Overview & Real-World Problem Solved
The **Log Search Tool** is a backend utility belonging to the "system" category.
**Problem it solves:** LLMs natively cannot interact with the outside world. Searches agent/tool/workflow logs. By exposing this tool to the AI, we bridge the gap between static text generation and dynamic, real-world execution.

---

## ⚙️ How It Works & Data Payload
When an Agent decides to use this tool, it must strictly adhere to the defined JSON schemas. The backend API validates the payload before execution.

### Input Payload Schema
`json
{"query":"string"}
``n
### Output Response Schema
`json
{"logs":"array"}
``n
**Data Flow**: The Agent outputs the Input Schema. The Python backend intercepts it, executes the underlying Python logic (e.g., HTTP request, DB query), formats the result into the Output Schema, and returns it to the Agent's context window.

---

## 🔗 Agent Connections & Interoperability
This tool can be attached to any Agent in the system via the "tools_enabled" array in the Agent's configuration.
*Synergy:* Tools in the "system" category pair exceptionally well with reporting agents (to write results) or analytical agents (to read results).

---

## 🔒 Security & Configuration
Security is paramount when allowing AI to execute code.
- **Requires Authentication**: No
- **Safe Mock Mode Supported**: No

### Environment Variables
To use this tool in production, the following environment variables MUST be configured in your ".env" file or Docker container:
- *No special environment variables required.*

If variables are missing and Safe Mock Mode is enabled, the tool will intercept the AI's request and return a simulated success response to prevent the system from crashing.

---

## 💾 Logging
Every invocation of this tool is recorded in the **PostgreSQL** database under the "tool_calls" payload inside "agent_steps". This ensures a full forensic audit trail of exactly what the AI executed, what inputs it provided, and how long the tool took to respond.

---

## 💼 Professional Usage Guide
To leverage this tool professionally:
1. Always test in **Safe Mock Mode** first to ensure the Agent understands the schema without mutating real data.
2. If this tool interacts with rate-limited external APIs, ensure your Agent's prompt explicitly instructs it to "Minimize calls to log_search_tool" to save costs.

