# WhatsApp Business Tool ($(@{name=WhatsApp Business Tool; slug=whatsapp_tool; description=Architecture for WhatsApp Business Cloud API. Use mock mode if credentials are missing.; category=social; input_schema=; output_schema=; requires_auth=True; required_env_keys=System.Object[]; safe_mock_mode=True}.slug))

## 📖 Overview & Real-World Problem Solved
The **WhatsApp Business Tool** is a backend utility belonging to the "social" category.
**Problem it solves:** LLMs natively cannot interact with the outside world. Architecture for WhatsApp Business Cloud API. Use mock mode if credentials are missing. By exposing this tool to the AI, we bridge the gap between static text generation and dynamic, real-world execution.

---

## ⚙️ How It Works & Data Payload
When an Agent decides to use this tool, it must strictly adhere to the defined JSON schemas. The backend API validates the payload before execution.

### Input Payload Schema
`json
{"to_number":"string","message":"string"}
``n
### Output Response Schema
`json
{"result":"string"}
``n
**Data Flow**: The Agent outputs the Input Schema. The Python backend intercepts it, executes the underlying Python logic (e.g., HTTP request, DB query), formats the result into the Output Schema, and returns it to the Agent's context window.

---

## 🔗 Agent Connections & Interoperability
This tool can be attached to any Agent in the system via the "tools_enabled" array in the Agent's configuration.
*Synergy:* Tools in the "social" category pair exceptionally well with reporting agents (to write results) or analytical agents (to read results).

---

## 🔒 Security & Configuration
Security is paramount when allowing AI to execute code.
- **Requires Authentication**: Yes
- **Safe Mock Mode Supported**: Yes

### Environment Variables
To use this tool in production, the following environment variables MUST be configured in your ".env" file or Docker container:
- "WHATSAPP_API_TOKEN"
- "WHATSAPP_PHONE_NUMBER_ID"

If variables are missing and Safe Mock Mode is enabled, the tool will intercept the AI's request and return a simulated success response to prevent the system from crashing.

---

## 💾 Logging
Every invocation of this tool is recorded in the **PostgreSQL** database under the "tool_calls" payload inside "agent_steps". This ensures a full forensic audit trail of exactly what the AI executed, what inputs it provided, and how long the tool took to respond.

---

## 💼 Professional Usage Guide
To leverage this tool professionally:
1. Always test in **Safe Mock Mode** first to ensure the Agent understands the schema without mutating real data.
2. If this tool interacts with rate-limited external APIs, ensure your Agent's prompt explicitly instructs it to "Minimize calls to whatsapp_tool" to save costs.

