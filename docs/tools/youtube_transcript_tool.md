# YouTube Transcript Tool (`youtube_transcript_tool`)

## 📖 Overview & Real-World Problem Solved
The **YouTube Transcript Tool** is a backend utility belonging to the `web` category.
**Problem it solves:** LLMs natively cannot interact with the outside world, nor can they watch gigabytes of video to understand a YouTube clip. Downloading raw MP4 files and running massive ML models like OpenAI's Whisper is incredibly expensive and slow. By exposing this tool to the AI, we bridge the gap. This tool hooks directly into YouTube's API to rip the raw text transcripts and closed captions in milliseconds, allowing the LLM to instantly "read" a video.

---

## ⚙️ How It Works & Data Payload
When an Agent decides to use this tool, it must strictly adhere to the defined JSON schemas. The backend API validates the payload before execution.

### Input Payload Schema
```json
{
  "url": "string"
}
```

### Output Response Schema
```json
{
  "transcript": "string"
}
```

**Data Flow**: The Agent outputs the Input Schema (with a YouTube URL). The Python backend intercepts it, executes the underlying Python logic (parsing the Video ID and fetching the transcript via `youtube-transcript-api`), formats the result into the Output Schema, and returns it to the Agent's context window. 

---

## 🔗 Agent Connections & Interoperability
This tool can be attached to any Agent in the system via the `tools_enabled` array in the Agent's configuration. 
*Synergy:* Tools in the `web` category pair exceptionally well with reporting agents (to write results) or analytical agents (to read results). Specifically, the **End Truth Fact-Checker** utilizes this tool heavily to transcribe claims before verifying them.

---

## 🔒 Security & Configuration
Security is paramount when allowing AI to execute code.
- **Requires Authentication**: No
- **Safe Mock Mode Supported**: No

### Environment Variables
To use this tool in production, the following environment variables MUST be configured in your `.env` file or Docker container:
- *No special environment variables required.*

---

## 💾 Logging
Every invocation of this tool is recorded in the **PostgreSQL** database under the `tool_calls` payload inside `agent_steps`. This ensures a full forensic audit trail of exactly what the AI executed, what inputs it provided, and how long the tool took to respond.

---

## 💼 Professional Usage Guide
To leverage this tool professionally:
1. Since YouTube transcripts can be massively long, ensure your Agent's prompt explicitly instructs it to summarize the transcript immediately upon receiving it to prevent the context window from overflowing.
2. The tool has a hardcoded safety cutoff of 15,000 characters to protect your LLM API limits from being drained by 4-hour podcast transcripts.
