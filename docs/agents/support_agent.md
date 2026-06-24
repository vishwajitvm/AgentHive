# Customer Support Agent ($(@{name=Customer Support Agent; slug=support_agent; description=Answers customer questions using uploaded docs.; agent_type=support; tools_enabled=System.Object[]; prompt=You are a Support Agent. Answer politely based strictly on the provided documentation.; max_steps=6; timeout_seconds=90}.slug))

## 📖 Overview & Real-World Problem Solved
The **Customer Support Agent** is an advanced AI entity of type "support".
**Problem it solves:** Modern workflows often require manual intervention for "support" related tasks. Answers customer questions using uploaded docs. By automating this, organizations save hundreds of hours of manual labor, ensuring consistency and immediate response times.

---

## ⚙️ How It Works (Internal Execution Flow)
When triggered, this agent enters a strict ReAct (Reasoning and Acting) execution loop:
1. **Payload Reception**: It receives a JSON payload containing the "user_id", "session_id", and "input_query".
2. **Context Assembly**: The system retrieves the agent's core instructions:
   > "You are a Support Agent. Answer politely based strictly on the provided documentation."
3. **Execution Loop**: The LLM processes the instructions and decides if it needs external data. It will loop up to **6 times** before hitting a hard timeout of **90 seconds**.
4. **Action**: If it needs to act, it yields a Tool Call. The backend executes the tool and injects the Observation back into the prompt.

---

## 🔗 Tool Connections & Interoperability
This agent does not operate in isolation. It is strictly granted Role-Based Access Control (RBAC) to the following internal tools:
- **"vector_search_tool"**
- **"search_tool"**

*How to connect:* You can chain this agent to other agents using the Orchestrator. For instance, a Data Analyst agent can pass its final markdown report to this agent to perform subsequent actions.

---

## 💾 Data Storage & Logging
- **Memory**: This agent has "memory_enabled = True". Every interaction is embedded using the "embedding_tool" and stored in **PostgreSQL (pgvector)**. When the user returns, the agent retrieves past context.
- **Logging**: Every single thought, tool call, and latency metric is logged in the "agent_steps" table. Furthermore, console logs are scraped by **Promtail** and aggregated in **Loki** for developer debugging.

---

## 🔒 Security Configuration
- **Isolation**: The agent cannot access the internet or internal databases unless explicitly granted a tool.
- **Timeouts**: Hard-capped at 90s to prevent infinite loops and API budget exhaustion.

---

## 💼 Professional Usage Guide
To use the **Customer Support Agent** professionally:
1. Ensure all prerequisite tools are configured (e.g., if it uses email, ensure SMTP env vars are set).
2. Write hyper-specific prompts when calling the agent. Instead of "do my task", provide a strict schema constraint in your input query to force the agent to format its final answer predictably.

