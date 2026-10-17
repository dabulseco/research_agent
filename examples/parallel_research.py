"""Gather a Markdown source report through the anonymous Parallel Search MCP."""

import argparse
import asyncio
import json
import math
import sys
import uuid

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


ENDPOINT = "https://search.parallel.ai/mcp"
USER_AGENT = (
    "research_agent/parallel-source-example "
    "(+https://github.com/dabulseco/research_agent)"
)


def tool_payload(result):
    """Accept structured MCP output or its JSON text representation."""
    text = "\n".join(block.text for block in result.content if block.type == "text")
    if result.isError:
        raise RuntimeError(text or "Parallel returned a tool error.")
    payload = result.structuredContent
    if payload is None:
        payload = json.loads(text)
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("Parallel returned an unexpected result format.")
    return payload


def render_results(payload, heading):
    lines = [f"## {heading}", ""]
    if not payload["results"]:
        lines.extend(["No sources returned.", ""])
    for source in payload["results"]:
        lines.extend([
            f"### {source.get('title') or source['url']}",
            "",
            source["url"],
            "",
        ])
        if source.get("publish_date"):
            lines.extend([f"Published: {source['publish_date']}", ""])
        lines.extend(["\n\n".join(source.get("excerpts", [])), ""])
    for warning in payload.get("warnings") or []:
        lines.extend([f"Warning: {warning['message']}", ""])
    for error in payload.get("errors") or []:
        lines.extend([f"Fetch failed: {error['url']} ({error['error_type']})", ""])
    return "\n".join(lines)


async def gather_sources(query, objective, fetch_count, timeout):
    # This client deliberately has no API key, OAuth handler, or app imports.
    # One invocation is one research session; reuse its ID for search and fetch.
    session_id = str(uuid.uuid4())
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT}, timeout=timeout
    ) as client:
        async with streamable_http_client(ENDPOINT, http_client=client) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                search = tool_payload(await session.call_tool("web_search", {
                    "objective": objective,
                    "search_queries": [query],
                    "session_id": session_id,
                }))
                report = ["# Research sources", "", f"Query: {query}", "",
                          f"Objective: {objective}", "", render_results(search, "Search results")]
                urls = [item["url"] for item in search["results"][:fetch_count]]
                if urls:
                    fetched = tool_payload(await session.call_tool("web_fetch", {
                        "urls": urls,
                        "objective": objective[:200],
                        "search_queries": [query],
                        "session_id": session_id,
                    }))
                    report.append(render_results(fetched, "Page excerpts"))
                return "\n".join(report)


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("must not be blank")
    return value.strip()


def positive_timeout(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return number


def error_message(error):
    # The SDK's task groups can wrap the useful service/network error.
    children = getattr(error, "exceptions", None)
    if children:
        return "; ".join(error_message(child) for child in children)
    return str(error) or type(error).__name__


async def run(args):
    return await asyncio.wait_for(
        gather_sources(args.query, args.objective or args.query, args.fetch, args.timeout),
        timeout=args.timeout,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", type=nonempty, help="focused keyword query (3–6 words recommended)")
    parser.add_argument("--objective", type=nonempty, help="research gap or question to investigate")
    parser.add_argument("--fetch", type=int, choices=range(4), default=0,
                        help="fetch excerpts from the first 0–3 search results (default: 0)")
    parser.add_argument("--timeout", type=positive_timeout, default=60,
                        help="overall deadline in seconds (default: 60)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        report = asyncio.run(run(args))
    except asyncio.TimeoutError:
        print("Research timed out. Try a narrower query or a longer --timeout.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Research cancelled.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"Research failed: {error_message(error)}", file=sys.stderr)
        return 1
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
