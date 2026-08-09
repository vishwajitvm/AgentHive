import os
import httpx
import json
import socket
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from app.tools.base import BaseTool
from app.logging.logger import get_logger

logger = get_logger(__name__)

class WikipediaTool(BaseTool):
    @property
    def slug(self) -> str: return "wikipedia_tool"
    @property
    def name(self) -> str: return "Wikipedia Search & Summary"
    @property
    def description(self) -> str:
        return "Searches Wikipedia and fetches article summaries. Arguments: query (search title or keyword), lang (optional language code, default 'en')."

    async def run(self, **kwargs) -> str:
        query = kwargs.get("query", "").strip()
        lang = kwargs.get("lang", "en").strip().lower()
        if not query:
            return "Error: query parameter is required."

        try:
            # Try Wikipedia REST API summary endpoint first
            encoded_query = httpx.QueryParams({"q": query})
            summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
            headers = {"User-Agent": "AgentHiveBot/1.0 (contact@agenthive.internal)"}
            
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(summary_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title", query)
                    extract = data.get("extract", "")
                    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    return f"Wikipedia Summary: {title}\nURL: {page_url}\n\n{extract}"

                # Fallback to MediaWiki search API
                search_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
                resp_search = await client.get(search_url, headers=headers)
                if resp_search.status_code == 200:
                    search_data = resp_search.json()
                    results = search_data.get("query", {}).get("search", [])
                    if results:
                        top_title = results[0]["title"]
                        top_snippet = results[0].get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                        return f"Wikipedia Search Result for '{query}':\nTitle: {top_title}\nSnippet: {top_snippet}\n(Article URL: https://{lang}.wikipedia.org/wiki/{top_title.replace(' ', '_')})"

            return f"No Wikipedia article summary found for '{query}'."
        except Exception as e:
            return f"WikipediaTool error: {str(e)}"

class ArxivTool(BaseTool):
    @property
    def slug(self) -> str: return "arxiv_tool"
    @property
    def name(self) -> str: return "ArXiv Scientific Paper Search"
    @property
    def description(self) -> str:
        return "Searches scientific preprints and papers on ArXiv. Arguments: query (search string), max_results (optional integer, default 5)."

    async def run(self, **kwargs) -> str:
        query = kwargs.get("query", "").strip()
        max_results = int(kwargs.get("max_results", 5))
        if not query:
            return "Error: query parameter is required."

        try:
            url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return f"Error: ArXiv API returned status {resp.status_code}"

                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)
                if not entries:
                    return f"No ArXiv papers found for query '{query}'."

                results = []
                for idx, entry in enumerate(entries, 1):
                    title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                    summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
                    published = entry.find("atom:published", ns).text[:10] if entry.find("atom:published", ns) is not None else "N/A"
                    authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
                    link = entry.find("atom:id", ns).text.strip()
                    results.append(f"{idx}. {title}\n   Authors: {', '.join(authors[:3])}\n   Published: {published}\n   URL: {link}\n   Abstract: {summary[:300]}...")

                return f"ArXiv Search Results for '{query}':\n\n" + "\n\n".join(results)
        except Exception as e:
            return f"ArxivTool error: {str(e)}"

class RssReaderTool(BaseTool):
    @property
    def slug(self) -> str: return "rss_reader_tool"
    @property
    def name(self) -> str: return "RSS/Atom Feed Aggregator"
    @property
    def description(self) -> str:
        return "Parses RSS or Atom feeds from a feed URL. Arguments: url (feed URL), max_items (optional int, default 5)."

    async def run(self, **kwargs) -> str:
        url = kwargs.get("url", "").strip()
        max_items = int(kwargs.get("max_items", 5))
        if not url:
            return "Error: url parameter is required."

        try:
            try:
                import feedparser
                feed = feedparser.parse(url)
                if feed.entries:
                    feed_title = feed.feed.get("title", "RSS Feed")
                    items = []
                    for entry in feed.entries[:max_items]:
                        t = entry.get("title", "No Title")
                        link = entry.get("link", "")
                        pub = entry.get("published", entry.get("updated", "N/A"))
                        summary = entry.get("summary", entry.get("description", ""))[:200]
                        items.append(f"- Title: {t}\n  Published: {pub}\n  Link: {link}\n  Summary: {summary}")
                    return f"Feed: {feed_title} ({len(items)} items):\n\n" + "\n\n".join(items)
            except Exception:
                pass

            # Fallback to direct HTTP XML fetching
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return f"Error fetching RSS feed: HTTP status {resp.status_code}"

                root = ET.fromstring(resp.text)
                items = []
                channel = root.find("channel")
                items_nodes = channel.findall("item") if channel is not None else root.findall("{http://www.w3.org/2005/Atom}entry")
                
                for item in items_nodes[:max_items]:
                    t_node = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
                    l_node = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
                    title_text = t_node.text if t_node is not None else "No Title"
                    link_text = l_node.text if l_node is not None else (l_node.attrib.get("href", "") if l_node is not None else "")
                    items.append(f"- {title_text} ({link_text})")

                return f"Parsed RSS Feed ({len(items)} items):\n" + "\n".join(items)
        except Exception as e:
            return f"RssReaderTool error: {str(e)}"

class UrlCheckerTool(BaseTool):
    @property
    def slug(self) -> str: return "url_checker_tool"
    @property
    def name(self) -> str: return "URL & HTTP Header Inspector"
    @property
    def description(self) -> str:
        return "Checks HTTP status, response headers, redirects, and SSL status for a URL. Arguments: url."

    async def run(self, **kwargs) -> str:
        url = kwargs.get("url", "").strip()
        if not url:
            return "Error: url parameter is required."
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url)
                status_code = resp.status_code
                headers = dict(resp.headers)
                server = headers.get("server", "Unknown")
                content_type = headers.get("content-type", "Unknown")
                content_length = headers.get("content-length", f"{len(resp.content)} bytes")
                history = [str(r.url) for r in resp.history]

                res_str = [
                    f"URL Inspection Results for: {url}",
                    f"Final URL: {resp.url}",
                    f"Status Code: {status_code} ({resp.reason_phrase})",
                    f"Server: {server}",
                    f"Content-Type: {content_type}",
                    f"Content-Length: {content_length}",
                    f"Redirect Chain: {' -> '.join(history) if history else 'None (Direct)'}",
                    "Response Headers:",
                    json.dumps(dict(list(headers.items())[:10]), indent=2)
                ]
                return "\n".join(res_str)
        except Exception as e:
            return f"UrlCheckerTool error: {str(e)}"

class WeatherTool(BaseTool):
    @property
    def slug(self) -> str: return "weather_tool"
    @property
    def name(self) -> str: return "Open-Meteo Weather Forecast"
    @property
    def description(self) -> str:
        return "Fetches live weather forecasts via Open-Meteo API. Arguments: location (city name or 'lat,lon', e.g. 'London' or '51.50,-0.12')."

    async def run(self, **kwargs) -> str:
        location = kwargs.get("location", "").strip()
        if not location:
            return "Error: location parameter is required."

        try:
            lat, lon = None, None
            city_name = location

            if "," in location:
                parts = location.split(",")
                try:
                    lat, lon = float(parts[0]), float(parts[1])
                except ValueError:
                    pass

            async with httpx.AsyncClient(timeout=10) as client:
                if lat is None or lon is None:
                    # Geocode location string using Open-Meteo Geocoding API
                    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={httpx.QueryParams({'name': location})['name']}&count=1"
                    geo_resp = await client.get(geo_url)
                    if geo_resp.status_code == 200:
                        geo_data = geo_resp.json()
                        results = geo_data.get("results", [])
                        if results:
                            lat = results[0]["latitude"]
                            lon = results[0]["longitude"]
                            city_name = f"{results[0].get('name')}, {results[0].get('country', '')}"

                if lat is None or lon is None:
                    return f"Error: Could not resolve coordinates for location '{location}'."

                forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                resp = await client.get(forecast_url)
                if resp.status_code != 200:
                    return f"Error: Weather API status {resp.status_code}"

                data = resp.json()
                current = data.get("current_weather", {})
                temp = current.get("temperature", "N/A")
                windspeed = current.get("windspeed", "N/A")
                winddirection = current.get("winddirection", "N/A")
                weathercode = current.get("weathercode", "N/A")

                return (
                    f"Weather Forecast for {city_name} (Lat: {lat}, Lon: {lon}):\n"
                    f"- Temperature: {temp} °C\n"
                    f"- Wind Speed: {windspeed} km/h\n"
                    f"- Wind Direction: {winddirection}°\n"
                    f"- Weather Code: {weathercode}"
                )
        except Exception as e:
            return f"WeatherTool error: {str(e)}"

class DnsLookupTool(BaseTool):
    @property
    def slug(self) -> str: return "dns_lookup_tool"
    @property
    def name(self) -> str: return "DNS Record Lookup"
    @property
    def description(self) -> str:
        return "Resolves DNS records (A, AAAA, MX, TXT, CNAME, NS) for a domain. Arguments: domain, record_type (optional, default 'A')."

    async def run(self, **kwargs) -> str:
        domain = kwargs.get("domain", "").strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
        record_type = kwargs.get("record_type", "A").strip().upper()
        if not domain:
            return "Error: domain parameter is required."

        try:
            try:
                import dns.resolver
                answers = dns.resolver.resolve(domain, record_type)
                records = [str(rdata) for rdata in answers]
                return f"DNS {record_type} Records for '{domain}':\n" + "\n".join([f"- {r}" for r in records])
            except Exception:
                # Fallback to standard socket library for A record lookup
                ip = socket.gethostbyname(domain)
                return f"DNS Lookup for '{domain}' (A record socket fallback):\n- {ip}"
        except Exception as e:
            return f"DnsLookupTool error: {str(e)}"

class WhoisTool(BaseTool):
    @property
    def slug(self) -> str: return "whois_tool"
    @property
    def name(self) -> str: return "Domain WHOIS Info Parser"
    @property
    def description(self) -> str:
        return "Retrieves domain WHOIS registration information. Arguments: domain."

    async def run(self, **kwargs) -> str:
        domain = kwargs.get("domain", "").strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
        if not domain:
            return "Error: domain parameter is required."

        try:
            try:
                import whois
                w = whois.whois(domain)
                registrar = w.get("registrar", "N/A")
                creation_date = w.get("creation_date", "N/A")
                expiration_date = w.get("expiration_date", "N/A")
                name_servers = w.get("name_servers", "N/A")
                return (
                    f"WHOIS Info for '{domain}':\n"
                    f"- Registrar: {registrar}\n"
                    f"- Created: {creation_date}\n"
                    f"- Expires: {expiration_date}\n"
                    f"- Name Servers: {name_servers}"
                )
            except Exception:
                pass

            # Fallback WHOIS query via RDAP HTTP API (rdap.org)
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                rdap_url = f"https://rdap.org/domain/{domain}"
                resp = await client.get(rdap_url)
                if resp.status_code == 200:
                    data = resp.json()
                    handle = data.get("handle", "N/A")
                    port43 = data.get("port43", "N/A")
                    events = data.get("events", [])
                    dates = [f"{e.get('eventAction')}: {e.get('eventDate')}" for e in events]
                    return f"WHOIS/RDAP Info for '{domain}':\nHandle: {handle}\nPort43: {port43}\nEvents:\n" + "\n".join(dates)
            
            return f"WHOIS data unavailable for '{domain}'."
        except Exception as e:
            return f"WhoisTool error: {str(e)}"

class HackerNewsTool(BaseTool):
    @property
    def slug(self) -> str: return "hacker_news_tool"
    @property
    def name(self) -> str: return "HackerNews Story Search"
    @property
    def description(self) -> str:
        return "Fetches top, new, or best stories from HackerNews API. Arguments: category (top/new/best, default 'top'), limit (optional int, default 5)."

    async def run(self, **kwargs) -> str:
        category = kwargs.get("category", "top").strip().lower()
        limit = int(kwargs.get("limit", 5))
        if category not in ["top", "new", "best"]:
            category = "top"

        try:
            url = f"https://hacker-news.firebaseio.com/v0/{category}stories.json"
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return f"Error: HackerNews API status {resp.status_code}"

                story_ids = resp.json()[:limit]
                stories = []
                for sid in story_ids:
                    item_resp = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                    if item_resp.status_code == 200:
                        item = item_resp.json()
                        title = item.get("title", "No Title")
                        score = item.get("score", 0)
                        by = item.get("by", "unknown")
                        story_url = item.get("url", f"https://news.ycombinator.com/item?id={sid}")
                        comments = item.get("descendants", 0)
                        stories.append(f"- {title}\n  Points: {score} | By: {by} | Comments: {comments}\n  URL: {story_url}")

                return f"HackerNews ({category.capitalize()} Stories):\n\n" + "\n\n".join(stories)
        except Exception as e:
            return f"HackerNewsTool error: {str(e)}"

class GithubRepoTool(BaseTool):
    @property
    def slug(self) -> str: return "github_repo_tool"
    @property
    def name(self) -> str: return "GitHub Repository Inspector"
    @property
    def description(self) -> str:
        return "Inspects public GitHub repositories, commits, issues, or releases. Arguments: repo ('owner/repo'), action ('info'/'commits'/'issues'/'releases', default 'info'), limit (optional int, default 5)."

    async def run(self, **kwargs) -> str:
        repo = kwargs.get("repo", "").strip().replace("https://github.com/", "")
        action = kwargs.get("action", "info").strip().lower()
        limit = int(kwargs.get("limit", 5))

        if not repo or "/" not in repo:
            return "Error: repo parameter must be in format 'owner/repo'."

        headers = {"User-Agent": "AgentHiveBot/1.0", "Accept": "application/vnd.github.v3+json"}
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                if action == "info":
                    api_url = f"https://api.github.com/repos/{repo}"
                    resp = await client.get(api_url, headers=headers)
                    if resp.status_code != 200:
                        return f"GitHub API error: status {resp.status_code} for repo '{repo}'"
                    d = resp.json()
                    return (
                        f"GitHub Repo: {d.get('full_name')}\n"
                        f"Description: {d.get('description', 'N/A')}\n"
                        f"Stars: {d.get('stargazers_count')} | Forks: {d.get('forks_count')} | Open Issues: {d.get('open_issues_count')}\n"
                        f"Language: {d.get('language')} | License: {d.get('license', {}).get('name') if d.get('license') else 'None'}\n"
                        f"Default Branch: {d.get('default_branch')}"
                    )
                elif action == "commits":
                    api_url = f"https://api.github.com/repos/{repo}/commits?per_page={limit}"
                    resp = await client.get(api_url, headers=headers)
                    if resp.status_code != 200: return f"GitHub API error: status {resp.status_code}"
                    commits = resp.json()
                    lines = [f"- {c['sha'][:7]}: {c['commit']['message'].splitlines()[0]} ({c['commit']['author']['name']})" for c in commits]
                    return f"Latest Commits for '{repo}':\n" + "\n".join(lines)
                elif action == "issues":
                    api_url = f"https://api.github.com/repos/{repo}/issues?per_page={limit}&state=open"
                    resp = await client.get(api_url, headers=headers)
                    if resp.status_code != 200: return f"GitHub API error: status {resp.status_code}"
                    issues = resp.json()
                    lines = [f"- #{i['number']}: {i['title']} (by {i['user']['login']})" for i in issues]
                    return f"Open Issues for '{repo}':\n" + "\n".join(lines)
                elif action == "releases":
                    api_url = f"https://api.github.com/repos/{repo}/releases?per_page={limit}"
                    resp = await client.get(api_url, headers=headers)
                    if resp.status_code != 200: return f"GitHub API error: status {resp.status_code}"
                    releases = resp.json()
                    lines = [f"- {r['tag_name']}: {r.get('name', 'Release')} ({r['published_at'][:10]})" for r in releases]
                    return f"Releases for '{repo}':\n" + "\n".join(lines) if lines else f"No releases found for '{repo}'."
                else:
                    return f"Error: Invalid action '{action}'. Supported: info, commits, issues, releases."
        except Exception as e:
            return f"GithubRepoTool error: {str(e)}"
