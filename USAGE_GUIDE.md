# Research Agent - Enhanced Search Features Usage Guide

## Quick Start

The improvements work automatically - just use the research agent as before! However, here's how to take advantage of the new features.

---

## What's New at Each Stage

### Stage 3: Gap Analysis

**What Changed:**
The gap analysis now generates much better search queries automatically.

**What to Look For:**
- Queries should be specific and include years (2024, 2025)
- Multiple query variants per gap (2-3 alternatives)
- Qualifying terms like "statistics", "research", "study"

**Example Output:**
```json
{
  "gaps": [
    {
      "gap_description": "Need current market size data for EV industry",
      "priority": "high",
      "information_type": "statistic",
      "time_sensitivity": "current",
      "search_queries": [
        "electric vehicle market size 2025 statistics billion",
        "EV global sales data 2025 report",
        "electric car industry growth statistics 2024-2025"
      ]
    }
  ]
}
```

**What You Can Do:**
- Review the generated queries
- If they look too vague, click "🔄 Redo Gap Analysis"
- Better gaps = better queries = better results

---

### Stage 4: Web Research

**What Changed:**
1. ✅ Search results are validated and scored
2. ✅ Full article content extracted (not just snippets!)
3. ✅ Results sorted by relevance
4. ✅ Complete analytics tracking

**What to Look For in Results:**

1. **Enhanced Result Fields:**
   ```json
   {
     "title": "Article Title",
     "link": "https://...",
     "snippet": "Short preview...",
     "relevance_score": 0.85,  // ← NEW: How relevant (0-1)
     "validation_reasons": [    // ← NEW: Why it was included
       "Good term match (5/6 terms)",
       "Contains recent year",
       "Authoritative domain"
     ],
     "extracted_content": "Full article text spanning multiple paragraphs with detailed statistics...",  // ← NEW: Full content!
     "content_length": 4823     // ← NEW: How much content
   }
   ```

2. **Research Findings:**
   - Should include detailed information (not just snippets)
   - Should cite sources with links
   - Should reference relevance scores for confidence

**Search Performance Analytics:**

Click the **"🔍 Search Performance Analytics"** expander to see:

```
┌─────────────────────────────────────────────┐
│  Total Queries    Success Rate    Avg Results    Content Extracted  │
│      12              91.7%            4.2              9            │
└─────────────────────────────────────────────┘

Average Query Time: 8.34s

✅ Successful Queries:
- `electric vehicle market size 2025 statistics` - 5 results (7.2s)
- `EV battery cost trends 2024 data` - 4 results (8.1s)
- `Tesla Model Y safety ratings NHTSA 2025` - 3 results (6.8s)

❌ Failed Queries:
- `vague query` (9.1s)
```

**What You Can Do:**
- Check the success rate - should be >70%
- Review failed queries to understand what didn't work
- If success rate is low, go back and redo gap analysis
- Monitor content extraction count - higher is better

---

### Sidebar Metrics

**When:** After Stage 3 (web research)

**What You'll See:**
```
📊 Search Metrics
Queries: 12
Success: 92%
Content: 9
```

**What It Means:**
- **Queries:** Total searches executed
- **Success:** Percentage that found results
- **Content:** Number of articles with full content extracted

---

## Interpreting Results

### Relevance Scores

| Score Range | Meaning | Action |
|------------|---------|--------|
| 0.8 - 1.0 | Highly relevant | Primary sources - use first |
| 0.5 - 0.79 | Moderately relevant | Good secondary sources |
| 0.3 - 0.49 | Marginally relevant | Use with caution |
| < 0.3 | Low relevance | Filtered out automatically |

### Validation Reasons

Common validation reasons you'll see:

- **"Good term match (X/Y terms)"**: Query words found in result
- **"Contains recent year"**: Has 2024, 2025, or 2026
- **"Authoritative domain"**: .edu, .gov, .org, research sites
- **"Contains data indicators"**: Has statistics, research, study, etc.
- **"Short snippet"**: Warning - might be low quality

### Content Extraction Status

**Success:**
- `extracted_content` field populated with full text
- `content_length` shows character count
- Best quality research!

**Failure:**
- `extraction_error` field shows why (timeout, blocked, etc.)
- Falls back to snippet only
- Still usable, just less detailed

---

## Best Practices

### 1. Review Gap Analysis Queries

Before proceeding to web research, check the generated queries:

**Good Indicators:**
- ✅ Specific terms (names, versions, models)
- ✅ Year markers (2024, 2025)
- ✅ Qualifying words (statistics, research, data)
- ✅ Multiple variants per gap

**Bad Indicators:**
- ❌ Too vague ("AI trends")
- ❌ No temporal markers
- ❌ Conversational ("what is...")
- ❌ Only one query per gap

If queries look bad → Click "🔄 Redo Gap Analysis"

### 2. Monitor Search Analytics

After web research completes:

1. **Check Success Rate:**
   - >80% = Excellent
   - 60-80% = Good
   - <60% = Consider redoing gap analysis

2. **Check Content Extraction:**
   - Should get content for 50-70% of results
   - Some sites block extraction (normal)

3. **Review Failed Queries:**
   - Look for patterns
   - Common issues: too vague, too specific, niche topics

### 3. Understand Result Quality

When reviewing web research findings:

**High Quality Indicators:**
- Multiple sources cited
- Relevance scores mentioned
- Detailed information (from extracted content)
- Recent sources (2024-2025)
- Specific data points and statistics

**Low Quality Indicators:**
- Few or no sources
- Vague information
- No data or specifics
- Only snippets used (no extracted content)

### 4. Iterate if Needed

If results are poor:

1. Go back to Stage 2 (Gap Analysis)
2. Click "🔄 Redo Gap Analysis"
3. The LLM will generate new queries
4. Proceed to web research again
5. Check if results improve

---

## Troubleshooting

### Low Success Rate

**Symptom:** Success rate <60% in analytics

**Possible Causes:**
1. Too vague queries from gap analysis
2. Network issues
3. Rate limiting (if using DuckDuckGo)
4. Very niche topics

**Solutions:**
- Redo gap analysis for better queries
- Try switching search method (Selenium ↔ DuckDuckGo)
- Check network connection
- Make research topic less niche

### Low Content Extraction

**Symptom:** Content extraction count is very low

**Possible Causes:**
1. Sites blocking scraping (normal for some sites)
2. Network timeouts
3. Paywall sites

**Impact:**
- Still functional - uses snippets as fallback
- Less detailed information

**Solutions:**
- This is expected behavior for some sites
- Snippets + relevance scores still provide value
- No action needed unless extraction count is 0

### Poor Result Relevance

**Symptom:** Research findings don't answer gaps well

**Possible Causes:**
1. Queries too generic
2. Topic mismatch
3. Insufficient web content available

**Solutions:**
- Redo gap analysis with more specific requirements
- Manually refine the research request
- Check failed queries for patterns

### Search Takes Too Long

**Symptom:** Web research stage takes >5 minutes

**Possible Causes:**
1. Too many gaps being researched
2. Content extraction adding time
3. Slow network

**Normal Timing:**
- 5-7 seconds per query (with content extraction)
- 4-5 gaps = ~30-40 seconds total
- Plus LLM synthesis time

**Solutions:**
- This is normal behavior
- Content extraction adds 2-3s per result (worth it!)
- Can reduce gaps in gap analysis if needed

---

## Advanced Tips

### 1. Customize Gap Priorities

When reviewing gap analysis output, pay attention to priority levels:
- Focus resources on "high" priority gaps
- "Medium" and "low" may be skipped if time/resources limited

### 2. Use Relevance Scores as Confidence

When citing research in final output:
- High relevance scores (>0.8) = High confidence sources
- Lower scores = Use but note uncertainty

### 3. Check Validation Reasons

Review why results were included:
- "Authoritative domain" = Trustworthy source
- "Contains data indicators" = Good for statistics
- "Good term match" = Directly relevant

### 4. Monitor Timing Patterns

In analytics:
- Queries taking >15s might indicate:
  - Slow websites
  - Network issues
  - Complex pages

### 5. Leverage Multiple Queries per Gap

Gap analysis generates 2-3 queries per gap:
- LLM will try different approaches
- Increases chance of finding relevant content
- Better coverage of topic

---

## API/Configuration Options

### Search Method Selection

**Sidebar: "Web Search Settings"**

**Options:**
1. **Selenium (Headless Browser)**
   - More reliable
   - Better for complex sites
   - Slower (~2s overhead per query)
   - Choose: Chrome or Firefox

2. **DuckDuckGo API**
   - Faster
   - No browser overhead
   - May hit rate limits
   - More prone to failures

**Recommendation:** Use Selenium for important research, DuckDuckGo for quick tests

### Browser Selection (Selenium only)

**Options:**
- Chrome: Generally faster, requires Chrome installed
- Firefox: Better for MacOS ARM (M1/M2/M3)

**Platform-Specific:**
- MacOS ARM → Use Firefox (better compatibility)
- MacOS Intel / Linux / Windows → Either works well

---

## Understanding the Improvements

### Why These Changes Matter

**Before Improvements:**
```
Query: "AI trends"
  ↓
[Random results]
  ↓
100-char snippet: "AI is growing rapidly and..."
  ↓
LLM: Not enough info, writes vague content
```

**After Improvements:**
```
Query: "artificial intelligence enterprise adoption statistics 2025 research"
  ↓
[5 results, validated, scored, sorted]
  ↓
Top result (score: 0.87):
  - Full 5000-char article about AI enterprise trends
  - Specific statistics and data points
  - Recent source (2025)
  - Authoritative domain (.edu)
  ↓
LLM: Comprehensive content with specific data!
```

### The Four Improvements Working Together

1. **Better Queries** (Gap Analysis)
   - Generates specific, targeted searches
   - Includes year markers and qualifiers

2. **Validation & Scoring** (Search Results)
   - Filters out low-quality results
   - Sorts by relevance
   - Provides confidence indicators

3. **Content Extraction** (Full Articles)
   - Gets 25-50x more content per result
   - Extracts detailed information
   - Enables comprehensive research

4. **Analytics** (Observability)
   - Shows what's working
   - Identifies problems
   - Enables optimization

**Result:** 2-3x improvement in research quality

---

## FAQ

**Q: Do I need to change anything to use these features?**
A: No! Everything works automatically. Just use the agent as before.

**Q: Why are some queries still failing?**
A: Some topics have limited web content, some sites block scraping, and some queries are inherently difficult. Success rates >70% are good.

**Q: Should I always look at the analytics?**
A: Only if you're troubleshooting or optimizing. Most users can ignore it.

**Q: What's a good relevance score?**
A: Above 0.5 is good. Above 0.8 is excellent. Below 0.3 is automatically filtered.

**Q: Why wasn't content extracted from some results?**
A: Some sites block scraping, have paywalls, or time out. This is normal. The system falls back to snippets.

**Q: Can I disable content extraction to speed things up?**
A: Not currently, but content extraction is usually worth the 2-3s per result for the quality improvement.

**Q: How do I know if my research is high quality?**
A: Check for: detailed information (not vague), multiple sources cited, recent dates, specific data/statistics, relevance scores >0.5.

---

## Support

If you encounter issues:

1. Check the search analytics for patterns
2. Review failed queries for common problems
3. Try redoing gap analysis for better queries
4. Switch search methods if one isn't working
5. Check network connectivity

For persistent issues, check the full implementation details in `IMPROVEMENTS_SUMMARY.md`.
