import re
import difflib
from typing import Dict, Any, List
from collections import Counter
from app.tools.base import BaseTool
from app.logging.logger import get_logger

logger = get_logger(__name__)

class SentimentTool(BaseTool):
    @property
    def slug(self) -> str: return "sentiment_tool"
    @property
    def name(self) -> str: return "Sentiment & Tone Analyzer"
    @property
    def description(self) -> str:
        return "Analyzes sentiment polarity, emotion, and tone score of text. Arguments: text."

    async def run(self, **kwargs) -> str:
        text = kwargs.get("text", "").strip()
        if not text:
            return "Error: text parameter is required."

        try:
            pos_words = {"good", "great", "excellent", "amazing", "wonderful", "fantastic", "positive", "love", "awesome", "success", "happy", "best", "benefit", "efficient", "strong", "growth", "win", "impressive"}
            neg_words = {"bad", "terrible", "horrible", "awful", "poor", "negative", "hate", "fail", "failure", "sad", "worst", "loss", "defect", "broken", "issue", "error", "risk", "weak", "decline"}

            tokens = [w.lower() for w in re.findall(r'\b\w+\b', text)]
            total = len(tokens) or 1

            pos_count = sum(1 for t in tokens if t in pos_words)
            neg_count = sum(1 for t in tokens if t in neg_words)
            neu_count = total - (pos_count + neg_count)

            compound = (pos_count - neg_count) / max(1, pos_count + neg_count)
            pos_ratio = round(pos_count / total, 3)
            neg_ratio = round(neg_count / total, 3)
            neu_ratio = round(neu_count / total, 3)

            tone = "Neutral"
            if compound > 0.2: tone = "Positive / Optimistic"
            elif compound < -0.2: tone = "Negative / Critical"

            return (
                f"Sentiment Analysis Results:\n"
                f"- Overall Tone: {tone}\n"
                f"- Compound Score: {round(compound, 3)} (-1.0 to +1.0)\n"
                f"- Positive Ratio: {pos_ratio}\n"
                f"- Negative Ratio: {neg_ratio}\n"
                f"- Neutral Ratio: {neu_ratio}\n"
                f"- Word Count: {total} (Pos: {pos_count}, Neg: {neg_count})"
            )
        except Exception as e:
            return f"SentimentTool error: {str(e)}"

class TextSummarizerTool(BaseTool):
    @property
    def slug(self) -> str: return "text_summarizer_tool"
    @property
    def name(self) -> str: return "Extractive Text Summarizer"
    @property
    def description(self) -> str:
        return "Generates an extractive summary of long text by extracting key sentences. Arguments: text, num_sentences (optional int, default 3)."

    async def run(self, **kwargs) -> str:
        text = kwargs.get("text", "").strip()
        num_sentences = int(kwargs.get("num_sentences", 3))

        if not text:
            return "Error: text parameter is required."

        try:
            # Simple sentence splitting
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 10]
            if not sentences:
                return text[:500]
            if len(sentences) <= num_sentences:
                return "\n".join(sentences)

            # Word frequency scoring
            stopwords = {"the", "a", "an", "in", "on", "of", "and", "or", "is", "are", "to", "for", "with", "that", "this", "it", "as", "by", "at", "from", "be", "was", "were"}
            words = [w.lower() for w in re.findall(r'\b\w+\b', text) if w.lower() not in stopwords]
            freqs = Counter(words)

            sentence_scores = []
            for idx, sentence in enumerate(sentences):
                s_words = [w.lower() for w in re.findall(r'\b\w+\b', sentence)]
                score = sum(freqs.get(w, 0) for w in s_words) / max(1, len(s_words))
                sentence_scores.append((score, idx, sentence))

            # Sort by score descending, take top num_sentences, then re-sort by original position index
            sentence_scores.sort(key=lambda x: x[0], reverse=True)
            selected = sorted(sentence_scores[:num_sentences], key=lambda x: x[1])

            summary_sentences = [item[2] for item in selected]
            return f"Extractive Summary ({len(summary_sentences)} key sentences out of {len(sentences)}):\n\n" + "\n\n".join(summary_sentences)
        except Exception as e:
            return f"TextSummarizerTool error: {str(e)}"

class DiffTool(BaseTool):
    @property
    def slug(self) -> str: return "diff_tool"
    @property
    def name(self) -> str: return "Text & File Diff Comparison"
    @property
    def description(self) -> str:
        return "Computes unified or line-by-line diffs between two strings or text blocks. Arguments: text1, text2, label1 (optional, default 'Original'), label2 (optional, default 'Modified')."

    async def run(self, **kwargs) -> str:
        text1 = kwargs.get("text1", "")
        text2 = kwargs.get("text2", "")
        label1 = kwargs.get("label1", "Original")
        label2 = kwargs.get("label2", "Modified")

        if text1 is None or text2 is None:
            return "Error: text1 and text2 parameters are required."

        try:
            lines1 = text1.splitlines(keepends=True)
            lines2 = text2.splitlines(keepends=True)

            diff = list(difflib.unified_diff(lines1, lines2, fromfile=label1, tofile=label2))
            if not diff:
                return f"No differences found between '{label1}' and '{label2}'."

            return f"Unified Diff Output:\n\n" + "".join(diff[:500])
        except Exception as e:
            return f"DiffTool error: {str(e)}"

class KeywordExtractorTool(BaseTool):
    @property
    def slug(self) -> str: return "keyword_extractor_tool"
    @property
    def name(self) -> str: return "Keyword & TF-IDF Extractor"
    @property
    def description(self) -> str:
        return "Extracts key terms, n-grams, and term frequencies from text. Arguments: text, top_n (optional int, default 10)."

    async def run(self, **kwargs) -> str:
        text = kwargs.get("text", "").strip()
        top_n = int(kwargs.get("top_n", 10))

        if not text:
            return "Error: text parameter is required."

        try:
            stopwords = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from",
                "up", "about", "into", "over", "after", "is", "are", "was", "were", "be", "been", "being",
                "have", "has", "had", "do", "does", "did", "will", "would", "shall", "should", "may", "might",
                "must", "can", "could", "this", "that", "these", "those", "it", "its", "they", "them", "their"
            }

            words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', text) if w.lower() not in stopwords]
            total_words = len(words) or 1
            freqs = Counter(words)

            # Extract bigrams
            bigrams = []
            words_raw = re.findall(r'\b[a-zA-Z]{3,}\b', text)
            for i in range(len(words_raw) - 1):
                w1, w2 = words_raw[i].lower(), words_raw[i+1].lower()
                if w1 not in stopwords and w2 not in stopwords:
                    bigrams.append(f"{w1} {w2}")
            bigram_freqs = Counter(bigrams)

            top_unigrams = freqs.most_common(top_n)
            top_bigrams_list = bigram_freqs.most_common(top_n // 2)

            res = [f"Keyword & Term Frequency Analysis (Total Words: {total_words}):\n", "Top Keywords (Unigrams):"]
            for term, count in top_unigrams:
                tf = round(count / total_words, 4)
                res.append(f"- {term}: frequency={count}, TF={tf}")

            if top_bigrams_list:
                res.append("\nTop Key Phrases (Bigrams):")
                for phrase, count in top_bigrams_list:
                    res.append(f"- {phrase}: frequency={count}")

            return "\n".join(res)
        except Exception as e:
            return f"KeywordExtractorTool error: {str(e)}"

class MarkdownToHtmlTool(BaseTool):
    @property
    def slug(self) -> str: return "markdown_to_html_tool"
    @property
    def name(self) -> str: return "Markdown / HTML Converter"
    @property
    def description(self) -> str:
        return "Converts Markdown text to HTML or HTML to formatted Markdown. Arguments: action ('md_to_html'/'html_to_md'), content."

    async def run(self, **kwargs) -> str:
        action = kwargs.get("action", "md_to_html").strip().lower()
        content = kwargs.get("content") or kwargs.get("text") or kwargs.get("markdown_text") or ""
        content = str(content).strip()

        if not content:
            return "Error: content parameter is required."

        try:
            if action == "md_to_html":
                try:
                    import markdown
                    html = markdown.markdown(content, extensions=['tables', 'fenced_code', 'toc'])
                    return f"Converted HTML:\n```html\n{html}\n```"
                except Exception:
                    # Simple regex fallback converter
                    html = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    html = re.sub(r'^### (.*)$', r'<h3>\1</h3>', html, flags=re.M)
                    html = re.sub(r'^## (.*)$', r'<h2>\1</h2>', html, flags=re.M)
                    html = re.sub(r'^# (.*)$', r'<h1>\1</h1>', html, flags=re.M)
                    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
                    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
                    return f"Converted HTML (Basic Fallback):\n```html\n{html}\n```"

            elif action == "html_to_md":
                # Convert HTML to clean markdown text
                text = content
                text = re.sub(r'<h1>(.*?)</h1>', r'# \1\n', text, flags=re.I)
                text = re.sub(r'<h2>(.*?)</h2>', r'## \1\n', text, flags=re.I)
                text = re.sub(r'<h3>(.*?)</h3>', r'### \1\n', text, flags=re.I)
                text = re.sub(r'<strong>(.*?)</strong>|<b>(.*?)</b>', r'**\1\2**', text, flags=re.I)
                text = re.sub(r'<em>(.*?)</em>|<i>(.*?)</i>', r'*\1\2*', text, flags=re.I)
                text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text, flags=re.I)
                text = re.sub(r'<br\s*/?>', r'\n', text, flags=re.I)
                text = re.sub(r'<[^>]+>', '', text)
                return f"Converted Markdown:\n\n{text.strip()}"

            else:
                return f"Error: Invalid action '{action}'. Supported: md_to_html, html_to_md."
        except Exception as e:
            return f"MarkdownToHtmlTool error: {str(e)}"
