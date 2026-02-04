import os
import warnings

# CRITICAL: Set environment variables BEFORE importing crewai
os.environ['CREWAI_TELEMETRY_ENABLED'] = 'false'
os.environ['OTEL_SDK_DISABLED'] = 'true'
# Set dummy OpenAI key to prevent CrewAI from complaining
os.environ['OPENAI_API_KEY'] = 'sk-dummy-key-for-local-llm'
os.environ['OPENAI_MODEL_NAME'] = 'gpt-4'  # Dummy model name
# Disable interactive prompts
os.environ['CREWAI_DISABLE_TELEMETRY_PROMPT'] = 'true'
os.environ['CREWAI_STORAGE_DIR'] = './.crewai_storage'

# Suppress deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import streamlit as st
from crewai import Agent, Task, Crew, Process

try:
    from langchain_ollama import OllamaLLM
except ImportError:
    # Fallback to old import if langchain-ollama not installed
    from langchain_community.llms import Ollama as OllamaLLM

from crewai.tools import BaseTool
from langchain_core.tools import Tool
from duckduckgo_search import DDGS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
import json
from datetime import datetime
import re
from bs4 import BeautifulSoup
import requests
import subprocess
import time
from urllib.parse import urlparse

# Initialize session state
if 'workflow_stage' not in st.session_state:
    st.session_state.workflow_stage = 0
if 'research_plan' not in st.session_state:
    st.session_state.research_plan = None
if 'initial_research' not in st.session_state:
    st.session_state.initial_research = None
if 'gap_analysis' not in st.session_state:
    st.session_state.gap_analysis = None
if 'web_research' not in st.session_state:
    st.session_state.web_research = None
if 'blog_post' not in st.session_state:
    st.session_state.blog_post = None
if 'html_output' not in st.session_state:
    st.session_state.html_output = None
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'browser_type' not in st.session_state:
    st.session_state.browser_type = "chrome"
if 'search_method' not in st.session_state:
    st.session_state.search_method = "selenium"
if 'search_metrics' not in st.session_state:
    st.session_state.search_metrics = {
        'queries_executed': 0,
        'queries_successful': 0,
        'total_results_found': 0,
        'failed_queries': [],
        'successful_queries': [],
        'query_times': [],
        'content_extracted': 0
    }

# Configure page
st.set_page_config(page_title="AI Research Agent", layout="wide")

# Function to get locally installed Ollama models
def get_installed_ollama_models():
    """Fetch list of locally installed Ollama models"""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Skip the header line and extract model names
            models = []
            for line in lines[1:]:  # Skip header
                if line.strip():
                    # Model name is the first column (includes tag like gemma3:27b)
                    parts = line.split()
                    if parts:
                        model_name = parts[0]  # Keep full name with tag
                        if model_name and model_name not in models:
                            models.append(model_name)
            
            if not models:
                st.error("No Ollama models found! Please install a model first.")
                st.code("ollama pull llama3.2", language="bash")
                return []
            return models
        else:
            st.warning("Could not fetch Ollama models. Make sure Ollama is running.")
            return []
    except FileNotFoundError:
        st.error("Ollama not found. Please install Ollama from https://ollama.ai")
        return []
    except subprocess.TimeoutExpired:
        st.warning("Ollama command timed out. Using default models.")
        return []
    except Exception as e:
        st.warning(f"Error fetching models: {str(e)}")
        return []

# Verify model exists in Ollama
def verify_model_exists(model_name):
    """Check if a model exists in Ollama"""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Check if model_name appears exactly in the output
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if parts and parts[0] == model_name:
                        return True
            return False
        return False
    except Exception:
        return False

# Content Extraction and Validation Functions
class ContentExtractor:
    """Extract main content from web pages"""

    def __init__(self):
        self.timeout = 10
        self.max_content_length = 5000

    def fetch_page_content(self, url: str) -> dict:
        """Fetch and extract main content from a URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script, style, and other non-content elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'ads']):
                tag.decompose()

            # Try to find main content areas
            main_content = None

            # Look for common content containers
            for selector in ['article', 'main', '[role="main"]', '.content', '.post', '.article']:
                content = soup.select_one(selector)
                if content:
                    main_content = content
                    break

            # Fallback to body
            if not main_content:
                main_content = soup.body

            if main_content:
                # Extract text
                text = main_content.get_text(separator='\n', strip=True)

                # Clean up extra whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = re.sub(r' +', ' ', text)

                # Limit length
                if len(text) > self.max_content_length:
                    text = text[:self.max_content_length] + "..."

                return {
                    'success': True,
                    'content': text,
                    'length': len(text),
                    'url': url
                }

            return {
                'success': False,
                'content': '',
                'error': 'No content found',
                'url': url
            }

        except requests.Timeout:
            return {
                'success': False,
                'content': '',
                'error': 'Request timeout',
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'content': '',
                'error': str(e),
                'url': url
            }

def validate_search_result(result: dict, query: str) -> dict:
    """
    Score and validate search result relevance
    Returns: dict with 'score' (0-1) and 'reasons' list
    """
    score = 0.0
    reasons = []

    # Extract query terms (remove common stop words and operators)
    stop_words = {'what', 'how', 'why', 'when', 'where', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'of', 'in', 'to', 'for'}
    query_terms = set([term.lower().strip('"') for term in query.split() if term.lower() not in stop_words and len(term) > 2])

    # Combine title and snippet for analysis
    result_text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()

    # Check term overlap - MORE LENIENT (give base score of 0.2 just for having a result)
    base_score = 0.2  # Start with base score
    score += base_score
    reasons.append("Search result returned")

    if query_terms:
        matching_terms = sum(1 for term in query_terms if term in result_text)
        term_score = matching_terms / len(query_terms)
        score += term_score * 0.3  # Reduced from 0.4 to be more lenient
        if term_score > 0.3:  # Lower threshold
            reasons.append(f"Term match ({matching_terms}/{len(query_terms)} terms)")
        elif matching_terms > 0:
            reasons.append(f"Partial term match ({matching_terms} terms)")

    # Boost recent content (2024, 2025, 2026)
    current_year = datetime.now().year
    recent_years = [str(current_year), str(current_year - 1), str(current_year - 2)]
    if any(year in result_text for year in recent_years):
        score += 0.15
        reasons.append("Contains recent year")

    # Check for authoritative domains
    url = result.get('link', '')
    authoritative_domains = ['.edu', '.gov', '.org', 'wikipedia.org', 'nature.com',
                            'science.org', 'ieee.org', 'acm.org', 'nih.gov', 'springer.com',
                            'elsevier.com', 'wiley.com', 'sage', 'academic', 'university']
    if any(domain in url.lower() for domain in authoritative_domains):
        score += 0.15
        reasons.append("Authoritative domain")

    # Check for data/statistics indicators - expanded list
    data_indicators = ['statistics', 'data', 'study', 'research', 'report', 'analysis',
                      'survey', 'findings', 'percent', '%', 'evaluation', 'assessment',
                      'curriculum', 'program', 'framework', 'implementation', 'case study']
    if any(indicator in result_text for indicator in data_indicators):
        score += 0.1
        reasons.append("Contains relevant keywords")

    # Check for academic/educational indicators
    academic_indicators = ['college', 'university', 'education', 'student', 'faculty',
                          'course', 'training', 'learning', 'teaching', 'academic']
    if any(indicator in result_text for indicator in academic_indicators):
        score += 0.1
        reasons.append("Educational content")

    # DON'T penalize short snippets as harshly (some academic sites have short snippets)
    snippet = result.get('snippet', '')
    if len(snippet) < 30:  # Only penalize VERY short snippets
        score *= 0.8  # Less harsh penalty
        reasons.append("Very short snippet")

    # Check title is not generic error
    title = result.get('title', '').lower()
    error_indicators = ['404', 'not found', 'error', 'no results', 'page not found']
    if any(indicator in title for indicator in error_indicators):
        score = 0.0
        reasons = ["Error page detected"]

    return {
        'score': min(score, 1.0),  # Cap at 1.0
        'reasons': reasons,
        'valid': score >= 0.2  # LOWERED threshold from 0.3 to 0.2 to be more inclusive
    }

def update_search_metrics(query: str, success: bool, num_results: int = 0,
                         elapsed_time: float = 0):
    """Update search metrics in session state"""
    metrics = st.session_state.search_metrics

    metrics['queries_executed'] += 1
    if success:
        metrics['queries_successful'] += 1
        metrics['total_results_found'] += num_results
        metrics['successful_queries'].append({
            'query': query,
            'results': num_results,
            'time': elapsed_time
        })
    else:
        metrics['failed_queries'].append({
            'query': query,
            'time': elapsed_time
        })

    if elapsed_time > 0:
        metrics['query_times'].append(elapsed_time)

# Initialize Ollama LLM
@st.cache_resource
def get_llm(model_name="llama2"):
    return OllamaLLM(
        model=model_name,
        base_url="http://localhost:11434",
        temperature=0.7
    )

# Selenium-based web search
class SeleniumSearcher:
    """Headless browser-based web search using Selenium"""
    
    def __init__(self, browser_type="chrome"):
        self.browser_type = browser_type
        self.driver = None
        self.is_mac_arm = self._check_mac_arm()
    
    def _check_mac_arm(self):
        """Check if running on Mac ARM (M1/M2/M3)"""
        import platform
        return platform.system() == 'Darwin' and platform.machine() == 'arm64'
    
    def _init_driver(self):
        """Initialize the webdriver"""
        try:
            if self.browser_type == "chrome":
                chrome_options = ChromeOptions()
                chrome_options.add_argument('--headless=new')  # New headless mode
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # MacOS ARM-specific settings
                if self.is_mac_arm:
                    chrome_options.add_argument('--disable-software-rasterizer')
                    chrome_options.add_argument('--disable-extensions')
                    # Don't use sandbox on Mac ARM due to compatibility issues
                    chrome_options.add_argument('--no-sandbox')
                
                try:
                    service = ChromeService(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e:
                    # Fallback: try without service
                    st.warning(f"ChromeDriver manager failed, trying system Chrome: {str(e)}")
                    self.driver = webdriver.Chrome(options=chrome_options)
                    
            else:  # firefox
                firefox_options = FirefoxOptions()
                firefox_options.add_argument('--headless')
                firefox_options.add_argument('--width=1920')
                firefox_options.add_argument('--height=1080')
                
                # MacOS-specific Firefox settings
                if self.is_mac_arm:
                    firefox_options.set_preference('media.navigator.enabled', False)
                    firefox_options.set_preference('media.peerconnection.enabled', False)
                
                try:
                    service = FirefoxService(GeckoDriverManager().install())
                    self.driver = webdriver.Firefox(service=service, options=firefox_options)
                except Exception as e:
                    # Fallback: try without service
                    st.warning(f"GeckoDriver manager failed, trying system Firefox: {str(e)}")
                    self.driver = webdriver.Firefox(options=firefox_options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize {self.browser_type} driver: {str(e)}")
            if self.is_mac_arm:
                st.info("💡 **MacOS M1/M2 Tip**: If Chrome fails, try Firefox or install Chrome for ARM from https://www.google.com/chrome/")
            return False
    
    def search_google(self, query, max_results=5):
        """Search using Google"""
        if not self.driver and not self._init_driver():
            return []
        
        results = []
        try:
            # Navigate to Google
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            self.driver.get(search_url)
            
            # Wait for results to load (with timeout)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))
                )
            except Exception:
                # If wait fails, still try to parse what loaded
                pass
            
            time.sleep(1)  # Small additional wait
            
            # Parse results
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find search result divs
            search_results = soup.find_all('div', class_='g')
            
            for result in search_results[:max_results]:
                try:
                    # Extract title
                    title_elem = result.find('h3')
                    title = title_elem.get_text() if title_elem else 'No title'
                    
                    # Extract link
                    link_elem = result.find('a')
                    link = link_elem.get('href') if link_elem else ''
                    
                    # Extract snippet
                    snippet_elem = result.find('div', class_=['VwiC3b', 'yXK7lf'])
                    snippet = snippet_elem.get_text() if snippet_elem else 'No snippet available'
                    
                    if title and link:
                        results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet
                        })
                except Exception:
                    continue
            
        except Exception as e:
            st.warning(f"Google search error: {str(e)}")
        
        return results
    
    def search_bing(self, query, max_results=5):
        """Search using Bing"""
        if not self.driver and not self._init_driver():
            return []
        
        results = []
        try:
            # Navigate to Bing
            search_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
            self.driver.get(search_url)
            
            # Wait for results
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li.b_algo"))
                )
            except Exception:
                pass
            
            time.sleep(1)
            
            # Parse results
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find search result items
            search_results = soup.find_all('li', class_='b_algo')
            
            for result in search_results[:max_results]:
                try:
                    title_elem = result.find('h2')
                    title = title_elem.get_text() if title_elem else 'No title'
                    
                    link_elem = result.find('a')
                    link = link_elem.get('href') if link_elem else ''
                    
                    snippet_elem = result.find('p')
                    snippet = snippet_elem.get_text() if snippet_elem else 'No snippet available'
                    
                    if title and link:
                        results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet
                        })
                except Exception:
                    continue
            
        except Exception as e:
            st.warning(f"Bing search error: {str(e)}")
        
        return results
    
    def close(self):
        """Close the webdriver"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

# Web search tool - CrewAI compatible with multiple backends
class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Search the web for information. Input should be a search query string. Returns top search results with titles, links, and snippets."
    
    def _run(self, query: str) -> str:
        """Search the web using selected method with validation and content extraction"""
        start_time = time.time()
        search_method = st.session_state.get('search_method', 'selenium')
        browser_type = st.session_state.get('browser_type', 'chrome')

        if search_method == 'selenium':
            result = self._selenium_search(query, browser_type)
        else:
            result = self._ddg_search(query)

        # Track elapsed time
        elapsed_time = time.time() - start_time

        # Parse results to check success
        try:
            results_list = json.loads(result)
            num_results = len([r for r in results_list if r.get('link', '')])
            success = num_results > 0 and 'error' not in results_list[0].get('title', '').lower()
            update_search_metrics(query, success, num_results, elapsed_time)
        except:
            update_search_metrics(query, False, 0, elapsed_time)

        return result
    
    def _selenium_search(self, query: str, browser_type: str) -> str:
        """Search using Selenium headless browser with validation and content extraction"""
        searcher = SeleniumSearcher(browser_type)
        extractor = ContentExtractor()

        try:
            # Try Google first
            results = searcher.search_google(query, max_results=5)

            # If Google fails, try Bing
            if not results:
                results = searcher.search_bing(query, max_results=5)

            if results:
                # Validate and score ALL results (even if they don't pass threshold)
                scored_results = []
                for result in results:
                    validation = validate_search_result(result, query)
                    result['relevance_score'] = validation['score']
                    result['validation_reasons'] = validation['reasons']
                    scored_results.append(result)

                # Sort by relevance score
                scored_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

                # If NO results pass validation threshold (0.3), still return top 3
                # but warn about low quality
                valid_results = [r for r in scored_results if r['relevance_score'] >= 0.3]

                if valid_results:
                    results_to_return = valid_results
                else:
                    # All results filtered - return top 3 anyway with warning
                    results_to_return = scored_results[:3]
                    for r in results_to_return:
                        r['low_quality_warning'] = 'This result scored below quality threshold but is included as best available'

                # Extract content from top 3 results
                for i, result in enumerate(results_to_return[:3]):
                    if result.get('link'):
                        content_data = extractor.fetch_page_content(result['link'])
                        if content_data['success']:
                            result['extracted_content'] = content_data['content']
                            result['content_length'] = content_data['length']
                            st.session_state.search_metrics['content_extracted'] += 1
                        else:
                            result['extraction_error'] = content_data.get('error', 'Unknown error')

                if results_to_return:
                    return json.dumps(results_to_return, indent=2)

            return json.dumps([{
                'title': 'No results found',
                'link': '',
                'snippet': f'No web results found for "{query}". Please try a different search query.'
            }], indent=2)

        except Exception as e:
            return json.dumps([{
                'title': 'Search error',
                'link': '',
                'snippet': f'Error searching for "{query}": {str(e)}'
            }], indent=2)
        finally:
            searcher.close()
    
    def _ddg_search(self, query: str) -> str:
        """Search using DuckDuckGo with retry logic, validation and content extraction"""
        extractor = ContentExtractor()

        for attempt in range(3):
            try:
                results = []
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(query, max_results=5))
                    for r in search_results:
                        results.append({
                            'title': r.get('title', 'No title'),
                            'link': r.get('href', ''),
                            'snippet': r.get('body', 'No snippet available')
                        })

                if results:
                    # Validate and score ALL results (even if they don't pass threshold)
                    scored_results = []
                    for result in results:
                        validation = validate_search_result(result, query)
                        result['relevance_score'] = validation['score']
                        result['validation_reasons'] = validation['reasons']
                        scored_results.append(result)

                    # Sort by relevance score
                    scored_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

                    # If NO results pass validation threshold (0.3), still return top 3
                    # but warn about low quality
                    valid_results = [r for r in scored_results if r['relevance_score'] >= 0.3]

                    if valid_results:
                        results_to_return = valid_results
                    else:
                        # All results filtered - return top 3 anyway with warning
                        results_to_return = scored_results[:3]
                        for r in results_to_return:
                            r['low_quality_warning'] = 'This result scored below quality threshold but is included as best available'

                    # Extract content from top 3 results
                    for i, result in enumerate(results_to_return[:3]):
                        if result.get('link'):
                            content_data = extractor.fetch_page_content(result['link'])
                            if content_data['success']:
                                result['extracted_content'] = content_data['content']
                                result['content_length'] = content_data['length']
                                st.session_state.search_metrics['content_extracted'] += 1
                            else:
                                result['extraction_error'] = content_data.get('error', 'Unknown error')

                    if results_to_return:
                        return json.dumps(results_to_return, indent=2)

                if attempt < 2:
                    time.sleep(2)

            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                    continue
                return json.dumps([{
                    'title': f'Search temporarily unavailable',
                    'link': '',
                    'snippet': f'Unable to perform web search for "{query}". Error: {str(e)}'
                }], indent=2)

        return json.dumps([{
            'title': 'No results found',
            'link': '',
            'snippet': f'No web results found for "{query}".'
        }], indent=2)

# Create search tool instance
search_tool = WebSearchTool()

# Step 1: Interpret Request and Create Research Plan
def step1_interpret_and_plan(user_request: str, llm):
    """Interpret user request and create research plan"""
    st.subheader("Step 1: Interpreting Request & Creating Research Plan")
    
    # Use string format for CrewAI LLM specification
    llm_string = f"ollama/{llm.model}"
    
    interpreter_agent = Agent(
        role='Research Request Interpreter',
        goal='Understand the user request and create a comprehensive research plan',
        backstory='You are an expert at understanding research needs and creating structured research plans.',
        llm=llm_string,
        verbose=True,
        allow_delegation=False
    )
    
    interpret_task = Task(
        description=f"""
        Analyze this research request: "{user_request}"
        
        Create a detailed research plan that includes:
        1. Main research questions (5-6 questions)
        2. Key topics to investigate
        3. Suggested search queries
        4. Expected information structure
        
        Format your response as a structured JSON with these keys:
        - main_questions: list of questions
        - topics: list of topics
        - search_queries: list of queries
        - structure: outline of expected information
        """,
        agent=interpreter_agent,
        expected_output="A structured research plan in JSON format"
    )
    
    crew = Crew(
        agents=[interpreter_agent],
        tasks=[interpret_task],
        process=Process.sequential,
        verbose=True,
        memory=False,
        cache=False,
        output_log_file=False
    )
    
    with st.spinner("Creating research plan..."):
        result = crew.kickoff()
    
    return str(result)

# Step 2: Execute Initial Research with Local LLM
def step2_initial_research(research_plan: str, llm):
    """Execute initial research using local LLM knowledge"""
    st.subheader("Step 2: Executing Initial Research (Local LLM)")
    
    llm_string = f"ollama/{llm.model}"
    
    researcher_agent = Agent(
        role='Knowledge Researcher',
        goal='Provide comprehensive information based on existing knowledge',
        backstory='You are a knowledgeable researcher who can synthesize information on various topics.',
        llm=llm_string,
        verbose=True,
        allow_delegation=False
    )
    
    research_task = Task(
        description=f"""
        Based on this research plan:
        {research_plan}
        
        Provide detailed information on each topic using your existing knowledge.
        Structure your response with:
        - Clear sections for each main question
        - Detailed explanations
        - Key facts and concepts
        - Note any areas where information might be limited or outdated
        """,
        agent=researcher_agent,
        expected_output="Comprehensive research report based on existing knowledge"
    )
    
    crew = Crew(
        agents=[researcher_agent],
        tasks=[research_task],
        process=Process.sequential,
        verbose=True,
        memory=False,
        cache=False,
        output_log_file=False
    )
    
    with st.spinner("Conducting initial research..."):
        result = crew.kickoff()
    
    return str(result)

# Step 3: Gap Analysis
def step3_gap_analysis(research_plan: str, initial_research: str, llm):
    """Analyze gaps in the initial research"""
    st.subheader("Step 3: Conducting Gap Analysis")
    
    llm_string = f"ollama/{llm.model}"
    
    analyst_agent = Agent(
        role='Research Gap Analyst',
        goal='Identify missing information and areas needing web research',
        backstory='You excel at identifying gaps in research and determining what additional information is needed.',
        llm=llm_string,
        verbose=True,
        allow_delegation=False
    )
    
    gap_task = Task(
        description=f"""
        Research Plan:
        {research_plan}

        Initial Research:
        {initial_research}

        Analyze the initial research and identify:
        1. Missing information or unanswered questions
        2. Areas where current information might be outdated
        3. Topics requiring recent data or statistics
        4. Specific search queries needed to fill gaps

        SEARCH QUERY BEST PRACTICES:
        When generating search queries, follow these rules to maximize relevance:

        1. BE SPECIFIC: Include exact names, technologies, versions, or models
           - Good: "Tesla Model Y safety ratings NHTSA 2025"
           - Bad: "electric car safety"

        2. ADD TEMPORAL MARKERS: Include year or recency indicators
           - Good: "machine learning trends 2025 statistics"
           - Bad: "machine learning trends"

        3. USE QUALIFYING TERMS: Add context words that indicate data quality
           - Include: "statistics", "data", "research", "study", "report", "analysis"
           - Good: "renewable energy adoption rate 2025 statistics"
           - Bad: "renewable energy"

        4. AVOID VAGUE QUESTIONS: Don't use conversational query formats
           - Good: "climate change impact agriculture yield statistics"
           - Bad: "how does climate change affect farming"

        5. INCLUDE DOMAIN INDICATORS: Add terms that help find authoritative sources
           - For science: "peer reviewed", "published research"
           - For data: "official statistics", "government report"
           - For tech: "documentation", "technical specifications"

        6. GENERATE MULTIPLE VARIANTS: Provide 2-3 alternative queries per gap
           - Different phrasings catch different sources
           - Mix general and specific terms

        GOOD QUERY EXAMPLES:
        - "quantum computing commercial applications 2025 report"
        - "artificial intelligence job market impact statistics 2025"
        - "coronavirus vaccine efficacy peer reviewed studies 2024"
        - "electric vehicle battery cost per kWh 2025 data"

        BAD QUERY EXAMPLES:
        - "what is quantum computing" (too basic/vague)
        - "AI" (too broad, no context)
        - "recent developments" (no specificity)
        - "how does it work" (conversational, unclear)

        Format as JSON with:
        {{
          "gaps": [
            {{
              "gap_description": "specific description of missing info",
              "priority": "high/medium/low",
              "information_type": "statistic/news/research/comparison/technical",
              "time_sensitivity": "current/recent/historical",
              "search_queries": ["query1", "query2", "query3"]
            }}
          ]
        }}
        """,
        agent=analyst_agent,
        expected_output="Gap analysis with prioritized, well-crafted search queries following best practices"
    )
    
    crew = Crew(
        agents=[analyst_agent],
        tasks=[gap_task],
        process=Process.sequential,
        verbose=True,
        memory=False,
        cache=False,
        output_log_file=False
    )
    
    with st.spinner("Analyzing research gaps..."):
        result = crew.kickoff()
    
    return str(result)

# Step 4: Web Research to Fill Gaps
def step4_web_research(gap_analysis: str, llm):
    """Conduct web searches to fill identified gaps"""
    st.subheader("Step 4: Conducting Web Research")
    
    llm_string = f"ollama/{llm.model}"
    
    web_researcher_agent = Agent(
        role='Web Research Specialist',
        goal='Find and synthesize information from the web to fill research gaps. If web search is unavailable, synthesize available information and note what could not be verified.',
        backstory='You are skilled at searching the web and extracting relevant information. When searches fail, you document what information is missing and work with available data.',
        llm=llm_string,
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=10  # Limit iterations to prevent excessive API calls
    )
    
    web_research_task = Task(
        description=f"""
        Gap Analysis:
        {gap_analysis}

        Use the web_search tool to find information for the most important identified gaps.

        UNDERSTANDING SEARCH RESULTS:
        The web_search tool returns enhanced results with:
        - title, link, snippet: Basic search result info
        - relevance_score: How well the result matches your query (0-1)
        - validation_reasons: Why this result was considered relevant
        - extracted_content: Full article text from the webpage (when available)
        - content_length: Length of extracted content

        USE THE EXTRACTED CONTENT for detailed information instead of just snippets!

        For each gap:
        1. Use the provided search queries (they're optimized for relevance)
        2. Review the extracted_content field for comprehensive information
        3. If extracted_content is available, use it for detailed facts and data
        4. If extraction failed, fall back to the snippet
        5. Cite sources using the provided links

        IMPORTANT:
        - Focus on 4-5 most critical gaps (high priority first)
        - Extracted content provides much more detail than snippets
        - Check relevance_score to prioritize which results to use
        - If a search fails, try alternative queries from the gap analysis
        - Document which gaps could not be filled and why

        Compile findings into a report that includes:
        - Detailed information from extracted content (not just snippets!)
        - Specific data, statistics, and facts found
        - Sources/links for all claims
        - Relevance scores to indicate confidence in sources
        - List of gaps that could not be filled and why
        """,
        agent=web_researcher_agent,
        expected_output="Comprehensive web research findings using full extracted content, with sources and confidence indicators"
    )
    
    crew = Crew(
        agents=[web_researcher_agent],
        tasks=[web_research_task],
        process=Process.sequential,
        verbose=True,
        memory=False,
        cache=False,
        output_log_file=False
    )
    
    with st.spinner("Searching the web for additional information..."):
        try:
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            error_msg = f"Web research encountered an error: {str(e)}\n\nProceeding with available information from earlier research phases."
            st.warning(error_msg)
            return error_msg

# Step 5: Create Blog Post
def step5_create_blog(research_plan: str, initial_research: str, web_research: str, llm):
    """Organize research into a comprehensive blog post"""
    st.subheader("Step 5: Creating Blog Post")
    
    llm_string = f"ollama/{llm.model}"
    
    writer_agent = Agent(
        role='Technical Writer',
        goal='Create a comprehensive, well-structured blog post with proper citations',
        backstory='You are an expert technical writer who creates engaging, informative content that is thorough and comprehensive.',
        llm=llm_string,
        verbose=True,
        allow_delegation=False
    )
    
    writing_task = Task(
        description=f"""
        Research Plan:
        {research_plan}
        
        Initial Research:
        {initial_research}
        
        Web Research:
        {web_research}
        
        Create a comprehensive blog post that:
        1. Has an engaging title and introduction
        2. Organizes information logically with clear sections
        3. Includes all relevant findings
        4. Cites sources properly (use [Source: URL] format)
        5. Has a conclusion summarizing key points
        6. Uses markdown formatting
        
        Make it informative, engaging, and well-structured.
        """,
        agent=writer_agent,
        expected_output="Complete blog post in markdown format with citations"
    )
    
    crew = Crew(
        agents=[writer_agent],
        tasks=[writing_task],
        process=Process.sequential,
        verbose=True,
        memory=False,
        cache=False,
        output_log_file=False
    )
    
    with st.spinner("Writing blog post..."):
        result = crew.kickoff()
    
    return str(result)

# Step 6: Convert to HTML5
def step6_convert_to_html(blog_post: str, llm):
    """Convert blog post to HTML5 with Bootstrap"""
    st.subheader("Step 6: Converting to HTML5")
    
    llm_string = f"ollama/{llm.model}"
    
    html_developer_agent = Agent(
        role='Frontend Developer',
        goal='Convert blog content to beautiful HTML5 with Bootstrap 5',
        backstory='You are a skilled frontend developer who creates responsive, attractive web pages.',
        llm=llm_string,
        verbose=True,
        allow_delegation=False
    )
    
    html_task = Task(
        description=f"""
        Blog Post Content:
        {blog_post}
        
        Convert this blog post to HTML5 using:
        1. Bootstrap 5 CSS framework
        2. Responsive design
        3. Proper semantic HTML5 tags
        4. Attractive styling and layout
        5. Interactive elements where appropriate
        6. Proper citation formatting
        
        Create a complete, standalone HTML file with:
        - DOCTYPE declaration
        - Bootstrap CDN links
        - Responsive meta tags
        - Custom CSS for styling
        - Optional JavaScript for interactivity
        
        Make it production-ready and visually appealing.
        """,
        agent=html_developer_agent,
        expected_output="Complete HTML5 document with Bootstrap 5"
    )
    
    crew = Crew(
        agents=[html_developer_agent],
        tasks=[html_task],
        process=Process.sequential,
        verbose=True,
        memory=False,
        cache=False,
        output_log_file=False
    )
    
    with st.spinner("Converting to HTML..."):
        result = crew.kickoff()
    
    return str(result)

# Main Streamlit App
def main():
    st.title("🤖 AI Research Agent")
    st.markdown("*Autonomous research agent with human-in-the-loop checkpoints*")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Get installed models
        installed_models = get_installed_ollama_models()
        
        if not installed_models:
            st.error("⚠️ No Ollama models found!")
            st.markdown("Please install a model first:")
            st.code("ollama pull llama2", language="bash")
            st.stop()
        
        # Model selection at the top
        model_name = st.selectbox(
            "🤖 Select Ollama Model",
            installed_models,
            help="Select from your locally installed Ollama models"
        )
        
        # Verify selected model exists
        if not verify_model_exists(model_name):
            st.error(f"⚠️ Model '{model_name}' not found in Ollama!")
            st.markdown(f"Install it with:")
            st.code(f"ollama pull {model_name}", language="bash")
            st.stop()
        
        # Show model info
        with st.expander("ℹ️ Model Information"):
            st.markdown(f"**Selected Model:** `{model_name}`")
            st.markdown(f"**Status:** ✅ Available")
            
            # Parse size from ollama list
            try:
                result = subprocess.run(
                    ['ollama', 'list'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if model_name in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                st.markdown(f"**Size:** {parts[2]}")
                            break
            except Exception:
                pass
            
            st.markdown("---")
            st.markdown("**Your Installed Models:**")
            for model in installed_models:
                if model == model_name:
                    st.markdown(f"- ✅ **{model}** (selected)")
                else:
                    st.markdown(f"- {model}")
            
            st.markdown("---")
            st.markdown("**Refresh models:** Restart the app after installing new models")
            st.markdown("**Install new model:**")
            st.code("ollama pull <model-name>", language="bash")
        
        st.markdown("---")
        st.markdown("### 🌐 Web Search Settings")
        
        enable_web_search = st.checkbox(
            "Enable Web Search",
            value=True,
            help="Uncheck to skip web research and rely only on local LLM knowledge"
        )
        
        if enable_web_search:
            search_method = st.radio(
                "Search Method",
                options=["selenium", "duckduckgo"],
                format_func=lambda x: "🌐 Selenium (Headless Browser)" if x == "selenium" else "🦆 DuckDuckGo API",
                help="Selenium is more reliable but slower. DuckDuckGo is faster but may be rate-limited."
            )
            st.session_state.search_method = search_method
            
            if search_method == "selenium":
                browser_type = st.selectbox(
                    "Browser",
                    options=["chrome", "firefox"],
                    format_func=lambda x: "🌐 Chrome" if x == "chrome" else "🦊 Firefox",
                    help="Choose which browser to use for headless searching"
                )
                st.session_state.browser_type = browser_type
                
                # Platform-specific guidance
                import platform
                if platform.system() == 'Darwin':  # MacOS
                    if platform.machine() == 'arm64':  # M1/M2/M3
                        st.info("🍎 **MacOS ARM Detected**\n\n"
                               "**Recommended:** Use Firefox for best compatibility\n\n"
                               "**Chrome issues?** Install ARM version from [google.com/chrome](https://www.google.com/chrome/)")
                    else:
                        st.info(f"🍎 **MacOS Intel** - Both browsers should work well")
                else:
                    st.info(f"💡 Using {browser_type.capitalize()} in headless mode")
            else:
                st.info("💡 Using DuckDuckGo API (may be rate-limited)")
        else:
            st.warning("⚠️ Web search disabled. Research will rely only on LLM knowledge.")
        
        if 'enable_web_search' not in st.session_state:
            st.session_state.enable_web_search = enable_web_search
        else:
            st.session_state.enable_web_search = enable_web_search
        
        st.markdown("---")
        st.markdown("### 📋 Workflow Stages")
        stages = [
            "0. Input Request",
            "1. Create Research Plan",
            "2. Initial Research",
            "3. Gap Analysis ✓",
            "4. Web Research ✓",
            "5. Create Blog Post ✓",
            "6. Convert to HTML"
        ]
        
        for i, stage in enumerate(stages):
            if i <= st.session_state.workflow_stage:
                st.markdown(f"**{stage}**")
            else:
                st.markdown(f"{stage}")
        
        st.markdown("---")
        # Search metrics summary in sidebar
        if st.session_state.workflow_stage >= 3:
            metrics = st.session_state.search_metrics
            if metrics['queries_executed'] > 0:
                st.markdown("### 📊 Search Metrics")
                success_rate = (metrics['queries_successful'] / metrics['queries_executed'] * 100) if metrics['queries_executed'] > 0 else 0
                st.markdown(f"**Queries:** {metrics['queries_executed']}")
                st.markdown(f"**Success:** {success_rate:.0f}%")
                st.markdown(f"**Content:** {metrics['content_extracted']}")
                st.markdown("---")

        if st.button("🔄 Reset Workflow"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    llm = get_llm(model_name)
    
    # Workflow stages
    if st.session_state.workflow_stage == 0:
        st.header("Step 0: Enter Your Research Request")
        user_input = st.text_area(
            "What would you like to research?",
            height=150,
            placeholder="Example: Research the latest developments in quantum computing and their potential applications in cryptography"
        )
        
        if st.button("🚀 Start Research", type="primary"):
            if user_input:
                st.session_state.user_input = user_input
                st.session_state.workflow_stage = 1
                st.rerun()
            else:
                st.warning("Please enter a research request")
    
    elif st.session_state.workflow_stage == 1:
        st.header("Step 1 & 2: Research Plan and Initial Research")
        
        if st.session_state.research_plan is None:
            st.session_state.research_plan = step1_interpret_and_plan(
                st.session_state.user_input, llm
            )
        
        st.subheader("Research Plan")
        st.text_area("Plan", st.session_state.research_plan, height=300)
        
        if st.session_state.initial_research is None:
            st.session_state.initial_research = step2_initial_research(
                st.session_state.research_plan, llm
            )
        
        st.subheader("Initial Research")
        st.text_area("Research", st.session_state.initial_research, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Proceed to Gap Analysis", type="primary"):
                st.session_state.workflow_stage = 2
                st.rerun()
        with col2:
            if st.button("🔄 Redo Research Plan"):
                st.session_state.research_plan = None
                st.session_state.initial_research = None
                st.rerun()
    
    elif st.session_state.workflow_stage == 2:
        st.header("Step 3: Gap Analysis")
        
        if st.session_state.gap_analysis is None:
            st.session_state.gap_analysis = step3_gap_analysis(
                st.session_state.research_plan,
                st.session_state.initial_research,
                llm
            )
        
        st.text_area("Gap Analysis", st.session_state.gap_analysis, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Proceed to Web Research", type="primary"):
                st.session_state.workflow_stage = 3
                st.rerun()
        with col2:
            if st.button("🔄 Redo Gap Analysis"):
                st.session_state.gap_analysis = None
                st.rerun()
    
    elif st.session_state.workflow_stage == 3:
        st.header("Step 4: Web Research")
        
        # Check if web search is enabled
        if not st.session_state.get('enable_web_search', True):
            st.warning("⚠️ Web search is disabled. Skipping to blog creation.")
            st.session_state.web_research = "Web search was disabled. Proceeding with information from initial research and gap analysis only."
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Proceed to Blog Creation", type="primary"):
                    st.session_state.workflow_stage = 4
                    st.rerun()
            with col2:
                if st.button("🔙 Back to Gap Analysis"):
                    st.session_state.workflow_stage = 2
                    st.rerun()
        else:
            if st.session_state.web_research is None:
                st.session_state.web_research = step4_web_research(
                    st.session_state.gap_analysis, llm
                )
            
            st.text_area("Web Research Findings", st.session_state.web_research, height=400)

            # Display search analytics
            metrics = st.session_state.search_metrics
            if metrics['queries_executed'] > 0:
                with st.expander("🔍 Search Performance Analytics", expanded=False):
                    # Summary metrics
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

                    with col_m1:
                        st.metric("Total Queries", metrics['queries_executed'])

                    with col_m2:
                        success_rate = (metrics['queries_successful'] / metrics['queries_executed'] * 100) if metrics['queries_executed'] > 0 else 0
                        st.metric("Success Rate", f"{success_rate:.1f}%")

                    with col_m3:
                        avg_results = (metrics['total_results_found'] / metrics['queries_successful']) if metrics['queries_successful'] > 0 else 0
                        st.metric("Avg Results/Query", f"{avg_results:.1f}")

                    with col_m4:
                        st.metric("Content Extracted", metrics['content_extracted'])

                    # Query timing
                    if metrics['query_times']:
                        avg_time = sum(metrics['query_times']) / len(metrics['query_times'])
                        st.markdown(f"**Average Query Time:** {avg_time:.2f}s")

                    # Successful queries
                    if metrics['successful_queries']:
                        st.markdown("**✅ Successful Queries:**")
                        for sq in metrics['successful_queries'][-5:]:  # Show last 5
                            st.markdown(f"- `{sq['query']}` - {sq['results']} results ({sq['time']:.2f}s)")

                    # Failed queries
                    if metrics['failed_queries']:
                        st.markdown("**❌ Failed Queries:**")
                        for fq in metrics['failed_queries'][-5:]:  # Show last 5
                            st.markdown(f"- `{fq['query']}` ({fq['time']:.2f}s)")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Proceed to Blog Creation", type="primary"):
                    st.session_state.workflow_stage = 4
                    st.rerun()
            with col2:
                if st.button("🔄 Redo Web Research"):
                    st.session_state.web_research = None
                    st.rerun()
    
    elif st.session_state.workflow_stage == 4:
        st.header("Step 5: Blog Post")
        
        if st.session_state.blog_post is None:
            st.session_state.blog_post = step5_create_blog(
                st.session_state.research_plan,
                st.session_state.initial_research,
                st.session_state.web_research,
                llm
            )
        
        st.markdown("### Blog Preview")
        st.markdown(st.session_state.blog_post)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Convert to HTML", type="primary"):
                st.session_state.workflow_stage = 5
                st.rerun()
        with col2:
            if st.button("🔄 Redo Blog Post"):
                st.session_state.blog_post = None
                st.rerun()
        with col3:
            st.download_button(
                "📥 Download Markdown",
                st.session_state.blog_post,
                file_name=f"blog_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
    
    elif st.session_state.workflow_stage == 5:
        st.header("Step 6: HTML5 Output")
        
        if st.session_state.html_output is None:
            st.session_state.html_output = step6_convert_to_html(
                st.session_state.blog_post, llm
            )
        
        st.subheader("HTML Code")
        st.code(st.session_state.html_output, language="html")
        
        st.subheader("Preview")
        st.components.v1.html(st.session_state.html_output, height=600, scrolling=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download HTML",
                st.session_state.html_output,
                file_name=f"blog_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )
        with col2:
            if st.button("🔄 Redo HTML Conversion"):
                st.session_state.html_output = None
                st.rerun()
        
        st.success("✅ Workflow Complete!")
        if st.button("🎉 Start New Research"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()

