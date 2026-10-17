# Optional source gathering with Parallel Search MCP

Use this standalone example to investigate a research gap before drafting a blog
post. It writes a Markdown report with source URLs, publication dates when
available, and excerpts. You can also fetch more focused excerpts from the first
few results.

[Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)
provides free web search and page fetching without an account or API key. Anonymous
search uses Fast mode. Free access has usage limits.

**Privacy:** this example uses a hosted service. Your query, objective, and URLs
selected for fetching are sent to Parallel. Use public research topics, not private
or sensitive information. It does not read your app session, local files, or model
configuration. The Streamlit application's search settings and local Ollama
workflow remain unchanged.

## Setup

Use Python 3.10 or newer. From the repository root, create a separate environment
and install only the example's dependencies. Ollama, CrewAI, and a browser are not
needed for this example.

```bash
python -m venv .venv-parallel
```

Activate it on macOS/Linux:

```bash
source .venv-parallel/bin/activate
```

Or in Windows PowerShell:

```powershell
.venv-parallel\Scripts\Activate.ps1
```

Then install:

```bash
python -m pip install -r examples/requirements-parallel.txt
```

## Gather sources for a research gap

Choose a focused query from Step 3's gap analysis, or enter one directly:

```bash
python examples/parallel_research.py "AI healthcare diagnostic accuracy"
```

To guide the search toward a specific question and read deeper into the first
result:

```bash
python examples/parallel_research.py "AI healthcare diagnostic accuracy" --objective "Find clinical evidence of benefits and limitations of AI-assisted diagnosis" --fetch 1
```

The example connects over Streamable HTTP to `https://search.parallel.ai/mcp`,
calls `web_search`, and optionally calls `web_fetch` for the first 1–3 results.
It reuses one session identifier across those calls and sends no authorization
header. By default it only searches, since search excerpts may already answer
your question.

Redirect standard output to save the report:

```bash
python examples/parallel_research.py "AI healthcare diagnostic accuracy" > sources.md
```

The report is written as UTF-8, including when output is redirected to a file.

Review the URLs, dates, and excerpts alongside the app's Web Research Findings
before writing or publishing. Verify claims against the original sources. This
example does not import the report into Streamlit or run the CrewAI workflow;
the report is a separate reference for your research and writing.

## Errors and limits

The overall deadline is 60 seconds. Use `--timeout 120` for a longer request, or
press Ctrl+C to cancel. Failed requests exit with status 1 and write diagnostics
to standard error; cancellation exits with status 130. A failed request does not
print a completed report, so check the exit status when redirecting output.

Service usage limits can reject a request. Read the error and wait before trying
again; the example does not automatically retry. Individual page extraction
failures appear as `Fetch failed` entries in an otherwise successful report.
An empty result set is reported as `No sources returned`.

## Check the example

After installing the example requirements, run its offline caller tests:

```bash
python -m unittest discover -s examples -p "test_parallel_research.py" -v
```

The tests use the real MCP client with a simulated HTTP service, so they do not
consume the free service's quota. Run one of the commands above separately to
check live access from your network.
