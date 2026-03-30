# research_agent
Crew.ai driven agent for local LLMs via Ollama with web search using Selenium headless browser. Blogs are created using results of the research and output as .md or .html files (updated: docx files). NOTE: only tested on Win11 so far!  Working on fixing a few minor bugs on MacOS (Mx chips).

As of Feb 3, 2026 the Mac bugs have been fixed (when search was updated). but it has not yet been tested on Win11 again.

# 🤖 AI Research Agent

A **fully local, privacy-first research automation tool** that uses CrewAI-orchestrated AI agents,
locally-running large language models (via Ollama), and a headless web browser (via Selenium) to
conduct multi-step research and generate publication-ready blog posts — all from a simple web interface.

> **No cloud API keys required.** Your data never leaves your machine.

---

## 📋 Table of Contents

- [What This Does](#what-this-does)
- [How It Works — The 7-Step Workflow](#how-it-works--the-7-step-workflow)
- [Key Features](#key-features)
- [Platform Support](#platform-support)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Using the App](#using-the-app)
- [Project Structure](#project-structure)
- [Configuration Options](#configuration-options)
- [Understanding the Output](#understanding-the-output)
- [Search Performance & Analytics](#search-performance--analytics)
- [Troubleshooting](#troubleshooting)
- [Additional Documentation](#additional-documentation)
- [License](#license)

---

## What This Does

You give the app a research topic (e.g., *"AI in healthcare diagnostics 2025"*), and it autonomously:

1. Plans a structured research strategy
2. Draws on the local AI model's existing knowledge
3. Identifies gaps where current web data is needed
4. Searches the live web to fill those gaps
5. Extracts full article text from top results
6. Synthesizes everything into a cited, structured blog post
7. Exports the final post as a `.md` (Markdown) or `.html` file

All AI processing runs locally through **Ollama** — no data is sent to OpenAI, Anthropic, or any
external service.

---

## How It Works — The 7-Step Workflow

The app follows a structured pipeline managed by [CrewAI](https://www.crewai.com/), which
coordinates multiple specialized AI agents working in sequence:

```
User Input → Plan → Research → Gap Analysis → Web Search → Blog Draft → HTML Export
   Step 1     Step 1  Step 2      Step 3        Step 4       Step 5      Step 6/7
```

### Step 1 — Interpret & Plan
A **Research Request Interpreter** agent analyzes your topic and generates a structured research
plan: main questions, key topics, and initial search queries.

### Step 2 — Initial Research (Local LLM)
A **Knowledge Researcher** agent uses the local AI model's built-in knowledge to provide a
first-pass report on all topics in the plan. This is entirely offline — no web access yet.

### Step 3 — Gap Analysis
A **Research Gap Analyst** agent compares the plan against the initial research and identifies:
- Missing or outdated information
- Topics requiring recent statistics or data
- Optimized web search queries to fill each gap (following best-practice query patterns)

### Step 4 — Web Research
A **Web Research Specialist** agent performs targeted web searches using either:
- **Selenium** (headless Chrome or Firefox) — searches Google then Bing as fallback
- **DuckDuckGo API** — faster, no browser required

Each result is scored for relevance (0–1), and full article text (up to 5,000 characters) is
extracted from the top results for much richer information than snippets alone.

### Step 5 — Blog Post Creation
A **Technical Writer** agent synthesizes all gathered information into a comprehensive,
properly-cited blog post.

### Step 6 — Markdown Output
The finished blog post is saved as a `.md` file and displayed in the app.

### Step 7 — HTML Export
The blog post is converted to a styled HTML file, ready to publish on any website.

---

## Key Features

- **Fully local AI** — runs any Ollama-compatible model (LLaMA, Gemma, Mistral, Qwen, etc.)
- **Dual search backends** — Selenium headless browser (Google + Bing) or DuckDuckGo API
- **Full-text content extraction** — retrieves complete article text, not just search snippets
- **Relevance scoring** — automatically filters low-quality search results
- **Search analytics dashboard** — tracks query success rates, timing, and content extraction
- **Multi-format output** — produces both Markdown (`.md`) and HTML (`.html`) files
- **Human-in-the-loop** — review and approve each step before proceeding
- **MacOS Apple Silicon support** — tested and working on M1/M2/M3 chips (as of Feb 2026)
- **Cross-platform** — Windows 11 (primary) and MacOS (fixed Feb 2026)

---

## Platform Support

| Platform | Status |
|----------|--------|
| Windows 11 | ✅ Primary development platform |
| MacOS (Apple Silicon M1/M2/M3) | ✅ Bug fixes applied Feb 2026 |
| macOS (Intel) | 🔄 Should work, not explicitly tested |
| Linux | 🔄 Should work with Chrome/Firefox installed |

---

## Technology Stack

| Component | Library/Tool | Purpose |
|-----------|-------------|---------|
| **AI Orchestration** | [CrewAI](https://www.crewai.com/) | Coordinates multiple AI agents into a workflow |
| **Local LLM** | [Ollama](https://ollama.ai/) | Runs AI models locally on your hardware |
| **LLM Interface** | [LangChain + langchain-ollama](https://python.langchain.com/) | Connects CrewAI to Ollama models |
| **Web UI** | [Streamlit](https://streamlit.io/) | Browser-based interface for the app |
| **Browser Automation** | [Selenium](https://selenium.dev/) | Controls headless Chrome/Firefox for web search |
| **Browser Management** | [webdriver-manager](https://pypi.org/project/webdriver-manager/) | Auto-installs the correct browser driver |
| **Web Scraping** | [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/) | Extracts clean text from web pages |
| **Fallback Search** | [duckduckgo-search](https://pypi.org/project/duckduckgo-search/) | API-based search without a browser |
| **HTTP Requests** | [requests](https://pypi.org/project/requests/) | Fetches web page content |

---

## Prerequisites

You need the following installed before setting up this project:

### 1. Python 3.9 or higher
- **Check:** `python --version`
- **Download:** https://www.python.org/downloads/

### 2. Ollama (local AI model runner)
Ollama allows you to download and run AI models directly on your computer — no internet
connection required once models are downloaded.

- **Install:** https://ollama.ai/download
- **Check it's running:** `ollama list`

After installing Ollama, pull at least one language model:

```bash
# Recommended starting models (choose based on your RAM):
ollama pull llama3.2          # ~2GB  — good for 8GB RAM
ollama pull gemma3:12b        # ~8GB  — better quality, needs 16GB RAM
ollama pull qwen2.5:14b       # ~9GB  — excellent at structured output
```

> 💡 **Tip:** Larger models produce better research quality but are slower. Start with `llama3.2`
> to test the workflow, then upgrade to a larger model for real research.

### 3. Google Chrome or Mozilla Firefox
Needed for the Selenium-based web search. At least one must be installed.

- **Chrome:** https://www.google.com/chrome/
- **Firefox:** https://www.mozilla.org/firefox/

> On **MacOS Apple Silicon**, if Chrome fails, try Firefox.

### 4. Git (to clone the repository)
- **Download:** https://git-scm.com/downloads

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/dabulseco/research_agent.git
cd research_agent
```

### Step 2 — Create a virtual environment (strongly recommended)

A virtual environment keeps this project's dependencies separate from other Python projects
on your computer.

```bash
# Create the virtual environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` appear at the start of your terminal prompt.

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

> This may take several minutes as it downloads all required libraries.
> If you see any errors, see the [Troubleshooting](#troubleshooting) section.

### Step 4 — Verify Ollama is running

Open a **separate terminal** and start Ollama if it isn't already running:

```bash
ollama serve
```

Then confirm you have at least one model available:

```bash
ollama list
```

---

## Running the Application

With your virtual environment activated and Ollama running, start the app:

```bash
streamlit run app.py
```

Your browser should automatically open to **http://localhost:8501**

If it doesn't open automatically, navigate there manually.

---

## Using the App

### Sidebar Settings
Before starting research, configure these settings in the left sidebar:

| Setting | Options | Recommendation |
|---------|---------|----------------|
| **AI Model** | Dropdown of your installed Ollama models | Use largest model your RAM supports |
| **Search Method** | Selenium (browser) / DuckDuckGo (API) | Selenium for better results; DuckDuckGo if Chrome/Firefox fails |
| **Browser** | Chrome / Firefox | Chrome first; Firefox as fallback on Mac |

### Step-by-Step Research Flow

1. **Enter your research topic** in the text box (be as specific as possible)
   - Example: *"Impact of AI tutoring systems on community college student outcomes 2024-2025"*
   - More specific = better research quality

2. **Click "Start Research"** — the app generates a research plan and shows it to you

3. **Review the plan** — read the proposed questions and search queries, then click **"Continue"**

4. **Initial research runs** — the local AI answers from its knowledge base

5. **Gap analysis runs** — the AI identifies what needs web verification

6. **Web search runs** — watch the progress bar; this is the slowest step (5–15 minutes)

7. **Blog post is generated** — review the draft

8. **Download your outputs:**
   - `.md` file — for note-taking apps, GitHub, or Obsidian
   - `.html` file — for publishing on a website

### Tips for Best Results

- Use specific topics with year ranges (e.g., "2024-2025")
- If success rate is below 60%, click "Redo Gap Analysis" to generate better queries
- Selenium search is slower but more reliable than DuckDuckGo
- Check the **Search Performance Analytics** panel after Step 4 to evaluate quality

---

## Project Structure

```
research_agent/
│
├── app.py                    # Main application — all agents, tools, and UI in one file
├── requirements.txt          # All Python package dependencies
│
├── README.md                 # This file
├── QUICK_REFERENCE.md        # One-page summary of enhanced search features
├── USAGE_GUIDE.md            # Detailed usage instructions and troubleshooting
├── IMPROVEMENTS_SUMMARY.md   # Technical notes on search enhancements
├── README_IMPROVEMENTS.md    # Overview of features added after initial release
├── BUGFIX_VALIDATION.md      # Log of bugs fixed (especially MacOS ARM fixes)
├── TESTING_CHECKLIST.md      # Manual testing checklist for contributors
│
├── readme.txt                # Original plain-text notes (pre-README.md)
├── LICENSE                   # MIT License
├── zz_bkup.zip               # Archived backup of earlier code version
└── __pycache__/              # Python bytecode cache (auto-generated, safe to ignore)
```

### Inside `app.py`

The entire application lives in a single Python file. Here is what each major section does:

| Section | What It Does |
|---------|-------------|
| **Environment setup** | Sets dummy OpenAI key (required by CrewAI even when using Ollama), disables telemetry |
| **Session state init** | Initializes Streamlit variables that persist between button clicks |
| **`get_installed_ollama_models()`** | Queries your local Ollama installation and populates the model dropdown |
| **`ContentExtractor` class** | Fetches full article text from URLs (up to 5,000 characters) using BeautifulSoup |
| **`validate_search_result()`** | Scores each search result from 0–1 based on relevance, recency, and domain authority |
| **`SeleniumSearcher` class** | Manages a headless Chrome or Firefox browser; searches Google then Bing as fallback |
| **`WebSearchTool` class** | CrewAI-compatible tool that wraps both search backends with validation and extraction |
| **`step1_interpret_and_plan()`** | CrewAI crew for Step 1 — research planning |
| **`step2_initial_research()`** | CrewAI crew for Step 2 — initial LLM-based research |
| **`step3_gap_analysis()`** | CrewAI crew for Step 3 — gap identification and query generation |
| **`step4_web_research()`** | CrewAI crew for Step 4 — live web searches |
| **`step5_create_blog()`** | CrewAI crew for Step 5 — blog post writing |
| **HTML generation** | Converts Markdown blog post to styled HTML |
| **Streamlit UI** | The sidebar, step controls, progress displays, analytics, and download buttons |

---

## Configuration Options

No configuration file is needed. All settings are managed through the app's sidebar UI. However,
a few things are hardcoded in `app.py` that you might want to adjust:

| Variable / Location | Default | What It Controls |
|---------------------|---------|-----------------|
| `max_content_length` in `ContentExtractor` | `5000` characters | How much text is extracted from each web page |
| `max_results` in search methods | `5` | How many search results are fetched per query |
| `max_iter` in web researcher agent | `10` | Maximum search iterations per Step 4 run |
| Ollama `base_url` in `get_llm()` | `http://localhost:11434` | Change if Ollama runs on a different port |
| `temperature` in `get_llm()` | `0.7` | LLM creativity level (0 = deterministic, 1 = creative) |

---

## Understanding the Output

### Markdown File (`.md`)
A structured blog post with:
- Introduction and context
- Sections for each major research question
- Inline citations with source URLs
- Conclusion and key takeaways

### HTML File (`.html`)
The same content rendered as a styled webpage. Open it in any browser or host it on any
static file server. No additional software required.

---

## Search Performance & Analytics

After Step 4 completes, expand the **"🔍 Search Performance Analytics"** panel to see:

| Metric | Target | What It Means |
|--------|--------|---------------|
| **Success Rate** | > 70% | Percentage of queries that returned usable results |
| **Content Extracted** | > 50% of results | How many pages yielded full article text |
| **Avg Relevance Score** | > 0.5 | Quality of search result matches (0–1) |
| **Query Time** | 5–10 seconds each | Normal range with content extraction enabled |

If success rate is below 60%, go back to Step 3 (Gap Analysis) and run it again — the AI will
generate new, more targeted queries.

---

## Troubleshooting

### Ollama errors / "No models found"
```bash
# Start Ollama
ollama serve

# Verify models are installed
ollama list

# Pull a model if none exist
ollama pull llama3.2
```

### Chrome / Selenium fails to start
- Try switching to **Firefox** in the sidebar
- On MacOS Apple Silicon: install Chrome for ARM from https://www.google.com/chrome/
- Switch search method to **DuckDuckGo** as a fallback (no browser required)

### `pip install` errors
Some packages require a C compiler. On Windows, install the
[Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
On Mac, run `xcode-select --install`.

### Research takes very long
This is normal for larger models. Each CrewAI step can take 2–10 minutes depending on:
- Your hardware (CPU vs GPU)
- The model size
- The number of web searches performed

### App crashes mid-research
Streamlit preserves session state between reruns. Try refreshing the page — previous step
results should still be visible. Reduce `max_iter` in Step 4's agent if crashes are frequent.

### "OPENAI_API_KEY" errors
This is expected behavior — CrewAI requires the environment variable to exist even when using
Ollama. The app sets a dummy key automatically. No real OpenAI API key is needed.

---

## Additional Documentation

The repository includes several supplementary documents for deeper reference:

| File | Contents |
|------|----------|
| `QUICK_REFERENCE.md` | One-page cheat sheet for the enhanced search system |
| `USAGE_GUIDE.md` | Detailed usage walkthrough with screenshots |
| `IMPROVEMENTS_SUMMARY.md` | Technical details on the search scoring and extraction system |
| `TESTING_CHECKLIST.md` | Manual QA checklist for verifying all features work correctly |
| `BUGFIX_VALIDATION.md` | Log of resolved bugs, particularly MacOS ARM compatibility fixes |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this software for any purpose, including commercial
use, as long as the original copyright notice is preserved.

---

*Built with CrewAI · Ollama · Streamlit · Selenium · Python*

*All AI processing is local — your research stays on your machine.*
