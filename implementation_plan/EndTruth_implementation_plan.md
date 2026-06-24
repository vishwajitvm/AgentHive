# Goal: Build the "End Truth" Fact-Checking Agent

The objective is to build a real-time fact-checking agent named **End Truth** that can take a URL (either an article or a video), ingest the content, and cross-reference the claims using web searches to verify authenticity. 

## Open Questions
> [!IMPORTANT]
> **Video Support:** For video transcription, the most reliable and lightweight method for public videos is using YouTube transcripts. Are we assuming the video URLs will primarily be YouTube links? If so, I will build a dedicated `youtube_transcript_tool`. If you need it to transcribe arbitrary `.mp4` video files from the web, we would need to integrate a heavy audio processing library like OpenAI's `Whisper`, which requires significant GPU resources or an external API key. I highly recommend starting with YouTube support first. Let me know your preference!

## Proposed Changes

### 1. New Tool: YouTube Transcript Tool
To handle video URLs, we need a way to extract the spoken text without downloading gigabytes of video. 
- **Add Dependency**: Add `youtube-transcript-api` to `backend/requirements.txt`.
- **Implement Tool**: Create a new tool that takes a YouTube URL, extracts the video ID, and pulls the closed captions/transcript as raw text.
- **Seed Tool**: Add `youtube_transcript_tool` to `backend/app/tools/seeder.py` so it registers in the database.

### 2. New Agent: End Truth Agent
We will create a specialized agent equipped with everything it needs to investigate claims.
- **Tools Enabled**: 
  - `youtube_transcript_tool` (for video URLs)
  - `scraper_tool` (for article URLs)
  - `search_tool` (to run web searches and fact-check)
  - `md_writer_tool` (to generate the final report)
- **Prompt Engineering**: The agent will be explicitly instructed to:
  1. Determine the content type (Article vs Video).
  2. Extract the text (via scraping or transcript).
  3. Identify the core factual claims.
  4. Run web searches to verify those claims against trusted sources.
  5. Return a "Truth Rating" and detailed breakdown.
- **Seed Agent**: Add `end_truth_agent` to `backend/app/agents/seeder.py`.

### 3. Documentation Updates
As requested, I will write highly detailed, professional markdown documentation for both the new tool and the new agent in the `docs/` folder, matching the new "Gold Standard" format we just established.
- **Create**: `docs/tools/youtube_transcript_tool.md`
- **Create**: `docs/agents/end_truth.md`

## Verification Plan
1. Update requirements and rebuild the backend Docker container if necessary.
2. Run the database seeders to inject the new tool and agent.
3. Test the tool logic manually to ensure it correctly parses YouTube URLs.
4. Verify the UI picks up the new agent automatically from the database.
