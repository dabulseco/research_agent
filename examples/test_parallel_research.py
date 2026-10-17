"""Exercise the CLI through the real MCP SDK without making network requests."""

import asyncio
import contextlib
import io
import json
import unittest
from unittest.mock import patch

import httpx

import parallel_research as example


REAL_CLIENT = httpx.AsyncClient
SOURCE = {
    "url": "https://example.org/clinical-study",
    "title": "Clinical study",
    "publish_date": "2026-01-10",
    "excerpts": ["Diagnostic accuracy improved in the study cohort."],
}


class MCPService:
    """An HTTP boundary fixture, including MCP initialization and discovery."""

    def __init__(self, *, tool_error=False, network_error=False, slow=False,
                 empty=False, fetch_error=False, text_only=False, malformed=False):
        self.requests = []
        self.tool_error = tool_error
        self.network_error = network_error
        self.slow = slow
        self.empty = empty
        self.fetch_error = fetch_error
        self.text_only = text_only
        self.malformed = malformed
        self.cancelled = False
        self.started = asyncio.Event()

    async def handle(self, request):
        self.requests.append(request)
        if request.method != "POST":
            return httpx.Response(405)
        message = json.loads(request.content)
        method = message["method"]
        if method.startswith("notifications/"):
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": message["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "parallel-fixture", "version": "1"},
            }
        elif method == "tools/list":
            result = {"tools": [
                {"name": name, "inputSchema": {"type": "object"}}
                for name in ("web_search", "web_fetch")
            ]}
        elif method == "tools/call":
            self.started.set()
            if self.network_error:
                raise httpx.ReadTimeout("fixture network timeout", request=request)
            if self.slow:
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    self.cancelled = True
                    raise
            if self.tool_error:
                result = {"isError": True, "content": [
                    {"type": "text", "text": "Free usage limit reached; try again later."}
                ]}
            else:
                is_fetch = message["params"]["name"] == "web_fetch"
                payload = {"results": [] if self.empty else [SOURCE]}
                if is_fetch and self.fetch_error:
                    payload = {"results": [], "errors": [
                        {"url": SOURCE["url"], "error_type": "FETCH_ERROR"}
                    ]}
                if self.malformed:
                    payload = {"unexpected": "schema"}
                result = {"content": [{"type": "text", "text": json.dumps(payload)}]}
                if not self.text_only:
                    result["structuredContent"] = payload
        else:
            raise AssertionError(f"Unexpected MCP method: {method}")
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": message["id"], "result": result})

    def client(self, **kwargs):
        return REAL_CLIENT(transport=httpx.MockTransport(self.handle), **kwargs)

    def calls(self):
        return [json.loads(r.content)["params"] for r in self.requests
                if r.method == "POST" and json.loads(r.content)["method"] == "tools/call"]


class ResearchCLITests(unittest.TestCase):
    def invoke(self, service, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(example.httpx, "AsyncClient", side_effect=service.client), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = example.main(["AI healthcare diagnostic accuracy", *args])
        for request in service.requests:
            self.assertEqual(str(request.url), example.ENDPOINT)
            self.assertEqual(request.headers["User-Agent"], example.USER_AGENT)
            self.assertNotIn("Authorization", request.headers)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_cli_search_fetch_and_markdown_report(self):
        service = MCPService()
        # Unrelated environment credentials must never become request headers.
        with patch.dict("os.environ", {"PARALLEL_API_KEY": "unused-test-value"}):
            status, report, _ = self.invoke(service, "--fetch", "1", "--objective", "Find clinical evidence")
        self.assertEqual(status, 0)
        self.assertIn("# Research sources", report)
        self.assertIn(SOURCE["url"], report)
        self.assertIn(SOURCE["excerpts"][0], report)
        self.assertIn("Published: 2026-01-10", report)
        self.assertIn("## Page excerpts", report)
        calls = service.calls()
        self.assertEqual([call["name"] for call in calls], ["web_search", "web_fetch"])
        search, fetch = [call["arguments"] for call in calls]
        self.assertEqual(search["search_queries"], ["AI healthcare diagnostic accuracy"])
        self.assertEqual(search["objective"], "Find clinical evidence")
        self.assertEqual(fetch["urls"], [SOURCE["url"]])
        self.assertEqual(fetch["search_queries"], search["search_queries"])
        self.assertEqual(search["session_id"], fetch["session_id"])
        self.assertEqual(len(search["session_id"]), 36)

    def test_default_does_not_fetch(self):
        service = MCPService(text_only=True)
        status, report, _ = self.invoke(service)
        self.assertEqual(status, 0)
        self.assertIn(SOURCE["title"], report)
        self.assertEqual(len(service.calls()), 1)

    def test_redirected_report_is_utf8_even_with_ascii_locale(self):
        service = MCPService()
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="ascii")
        with patch.object(example.httpx, "AsyncClient", side_effect=service.client), \
                contextlib.redirect_stdout(stream):
            status = example.main(["clinical evidence", "--objective", "Find AI’s limitations"])
        stream.flush()
        self.assertEqual(status, 0)
        self.assertIn("AI’s limitations", buffer.getvalue().decode("utf-8"))

    def test_empty_search_does_not_fetch(self):
        service = MCPService(empty=True)
        status, report, _ = self.invoke(service, "--fetch", "3")
        self.assertEqual(status, 0)
        self.assertIn("No sources returned.", report)
        self.assertEqual(len(service.calls()), 1)

    def test_page_error_retains_search_sources_and_explains_failure(self):
        status, report, _ = self.invoke(MCPService(fetch_error=True), "--fetch", "1")
        self.assertEqual(status, 0)
        self.assertIn(SOURCE["excerpts"][0], report)
        self.assertIn(f"Fetch failed: {SOURCE['url']} (FETCH_ERROR)", report)

    def test_tool_error_fails_without_report_or_retry(self):
        service = MCPService(tool_error=True)
        status, report, error = self.invoke(service)
        self.assertEqual(status, 1)
        self.assertEqual(report, "")
        self.assertIn("Free usage limit reached", error)
        self.assertEqual(len(service.calls()), 1)

    def test_malformed_output_fails_without_report(self):
        status, report, error = self.invoke(MCPService(malformed=True))
        self.assertEqual(status, 1)
        self.assertEqual(report, "")
        self.assertIn("unexpected result format", error)

    def test_network_timeout_fails_without_report(self):
        status, report, error = self.invoke(MCPService(network_error=True))
        self.assertEqual(status, 1)
        self.assertEqual(report, "")
        self.assertIn("fixture network timeout", error)

    def test_overall_timeout_cancels_inflight_request(self):
        service = MCPService(slow=True)
        status, report, error = self.invoke(service, "--timeout", "0.1")
        self.assertEqual(status, 1)
        self.assertEqual(report, "")
        self.assertIn("Research timed out", error)
        self.assertTrue(service.cancelled)

    def test_invalid_arguments_make_no_requests(self):
        for args in (["--timeout", "nan"], ["--timeout", "0"], ["--fetch", "4"]):
            service = MCPService()
            with self.subTest(args=args), self.assertRaises(SystemExit) as stopped:
                self.invoke(service, *args)
            self.assertEqual(stopped.exception.code, 2)
            self.assertEqual(service.requests, [])


class CancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancellation_propagates_and_closes_http_client(self):
        service = MCPService(slow=True)
        clients = []

        def create_client(**kwargs):
            client = service.client(**kwargs)
            clients.append(client)
            return client

        with patch.object(example.httpx, "AsyncClient", side_effect=create_client):
            task = asyncio.create_task(example.gather_sources("AI diagnostics evidence", "Find evidence", 0, 60))
            await asyncio.wait_for(service.started.wait(), timeout=5)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertTrue(service.cancelled)
        self.assertTrue(all(client.is_closed for client in clients))


if __name__ == "__main__":
    unittest.main()
