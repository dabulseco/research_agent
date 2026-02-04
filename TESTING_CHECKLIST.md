# Testing Checklist - Enhanced Search Features

## Quick Verification Tests

Run these tests to verify all improvements are working correctly.

---

## Test 1: Enhanced Query Generation

**Goal:** Verify gap analysis generates better queries

### Steps:
1. Start the app: `streamlit run app.py`
2. Enter research request: "Research the impact of artificial intelligence on healthcare in 2025"
3. Proceed through Stage 1 & 2 to Stage 3 (Gap Analysis)
4. Review the generated queries in the gap analysis output

### Expected Results:
✅ Queries should be specific: `"AI healthcare diagnostics accuracy 2025 statistics"`
✅ Include year markers: `"2025"`, `"2024"`
✅ Have qualifying terms: `"statistics"`, `"research"`, `"study"`, `"data"`
✅ Multiple variants per gap (2-3 queries)
✅ NOT vague: No queries like `"what is AI"` or just `"healthcare"`

### Pass/Fail Criteria:
- **Pass:** At least 80% of queries follow best practices
- **Fail:** Most queries are vague or missing year markers

---

## Test 2: Search Result Validation

**Goal:** Verify results are being validated and scored

### Steps:
1. Continue from Test 1 to Stage 4 (Web Research)
2. Let the web research complete
3. Look at the raw output or check the verbose logs in terminal

### Expected Results:
✅ Results include `relevance_score` field (0-1)
✅ Results include `validation_reasons` list
✅ Low-quality results filtered out (score < 0.3)
✅ Results sorted by relevance score (highest first)

### How to Check:
Look in terminal verbose output for JSON like:
```json
{
  "relevance_score": 0.87,
  "validation_reasons": ["Good term match (5/6 terms)", "Contains recent year"]
}
```

### Pass/Fail Criteria:
- **Pass:** Search results include validation fields
- **Fail:** Results missing relevance_score or validation_reasons

---

## Test 3: Content Extraction

**Goal:** Verify full article content is being extracted

### Steps:
1. Continue from Test 2 (already at Stage 4)
2. Check terminal verbose output for content extraction
3. Look for `extracted_content` field in results

### Expected Results:
✅ Top 3 results have `extracted_content` field
✅ Content length is substantial (1000-5000 chars)
✅ Content is readable article text (not HTML/garbage)
✅ Some results may fail extraction (normal) - check for `extraction_error`

### How to Check:
Terminal output should show:
```json
{
  "title": "Article Title",
  "extracted_content": "Full article text here spanning...",
  "content_length": 4823
}
```

Or for failures:
```json
{
  "extraction_error": "Request timeout"
}
```

### Pass/Fail Criteria:
- **Pass:** At least 50% of top results have extracted_content
- **Fail:** No results have extracted_content

---

## Test 4: Search Analytics Dashboard

**Goal:** Verify metrics are tracked and displayed

### Steps:
1. After web research completes (Stage 4)
2. Look for the expandable section: "🔍 Search Performance Analytics"
3. Click to expand
4. Check sidebar for metrics summary

### Expected Results:

**Main Dashboard (expandable):**
✅ Shows 4 metric cards:
  - Total Queries
  - Success Rate (percentage)
  - Avg Results/Query
  - Content Extracted

✅ Shows "Average Query Time" in seconds

✅ Lists recent successful queries with:
  - Query text
  - Number of results
  - Time taken

✅ Lists recent failed queries (if any) with:
  - Query text
  - Time taken

**Sidebar Summary:**
✅ Shows under "📊 Search Metrics":
  - Queries: [number]
  - Success: [percentage]
  - Content: [number]

### Pass/Fail Criteria:
- **Pass:** All metrics display correctly with reasonable values
- **Fail:** Metrics missing, showing 0, or not updating

---

## Test 5: End-to-End Quality

**Goal:** Verify overall improvement in research quality

### Steps:
1. Complete full workflow (Stage 0 → 6)
2. Review Stage 5 (Blog Post)
3. Compare quality to previous version

### Expected Results:
✅ Blog post includes specific data and statistics
✅ Multiple sources cited with [Source: URL] format
✅ Information is detailed (not just vague statements)
✅ Sources are recent (2024-2025 dates mentioned)
✅ Content addresses the research gaps identified

### Quality Indicators:
- **High Quality:**
  - Specific numbers, percentages, statistics
  - Multiple authoritative sources
  - Recent information
  - Detailed explanations

- **Low Quality:**
  - Vague statements ("AI is growing")
  - Few or no sources
  - Generic information
  - No specific data

### Pass/Fail Criteria:
- **Pass:** Blog post shows clear improvement with specific, sourced information
- **Fail:** Blog post is still vague with few sources

---

## Test 6: Different Search Methods

**Goal:** Verify both search methods work

### Test 6A: Selenium (Chrome)
1. Sidebar → "Search Method" → Select "Selenium"
2. Sidebar → "Browser" → Select "Chrome"
3. Run Stages 3-4
4. Verify searches complete successfully

### Test 6B: Selenium (Firefox)
1. Reset workflow (🔄 button)
2. Sidebar → "Search Method" → Select "Selenium"
3. Sidebar → "Browser" → Select "Firefox"
4. Run Stages 3-4
5. Verify searches complete successfully

### Test 6C: DuckDuckGo
1. Reset workflow
2. Sidebar → "Search Method" → Select "DuckDuckGo API"
3. Run Stages 3-4
4. Verify searches complete successfully

### Expected Results:
✅ All three methods complete without errors
✅ All three produce validated results with content extraction
✅ Success rates >60% for all methods

### Pass/Fail Criteria:
- **Pass:** All search methods work
- **Fail:** One or more methods fail consistently

---

## Test 7: Analytics Accuracy

**Goal:** Verify metrics are accurate

### Steps:
1. Note the queries executed during web research
2. Count manually:
   - How many queries ran
   - How many succeeded (got results)
   - How many failed
3. Compare to analytics dashboard

### Expected Results:
✅ Total queries matches your count
✅ Success/failure split matches your observation
✅ Content extracted count makes sense (0-3 per successful query)

### Pass/Fail Criteria:
- **Pass:** Metrics accurate within ±1 query
- **Fail:** Metrics significantly off

---

## Test 8: Error Handling

**Goal:** Verify graceful handling of failures

### Test 8A: Network Issues
1. Disconnect network temporarily
2. Run web research
3. Reconnect network

**Expected:** Should log errors but not crash, continue to next query

### Test 8B: Invalid Queries
1. Manually edit gap analysis to include gibberish query
2. Run web research

**Expected:** Query fails, shows in "Failed Queries" section, continues

### Test 8C: Rate Limiting (DuckDuckGo)
1. Use DuckDuckGo search method
2. Run multiple workflows quickly

**Expected:** May hit rate limit, shows in failed queries, doesn't crash

### Pass/Fail Criteria:
- **Pass:** App handles errors gracefully, continues execution
- **Fail:** App crashes on errors

---

## Performance Benchmarks

### Timing Expectations

| Operation | Expected Time | Acceptable Range |
|-----------|---------------|------------------|
| Single query (no extraction) | 3-5s | 2-8s |
| Single query (with extraction) | 5-7s | 4-10s |
| Full web research (5 gaps) | 30-40s | 20-60s |
| Content extraction (1 page) | 2-3s | 1-5s |

### Test Performance
1. Check "Average Query Time" in analytics
2. Should be in acceptable range above

**Pass:** Times within acceptable ranges
**Fail:** Times consistently >10s per query

---

## Regression Tests

### Verify Nothing Broke

**Test 9A: Stage 1 Still Works**
- Enter research request
- Verify research plan generates successfully
- Plan should have structure, questions, topics

**Test 9B: Stage 2 Still Works**
- Initial research completes
- Uses local LLM knowledge
- Produces comprehensive response

**Test 9C: Stage 5 Still Works**
- Blog post creation succeeds
- Combines all research sources
- Formats properly with sections

**Test 9D: Stage 6 Still Works**
- HTML conversion completes
- Valid HTML5 with Bootstrap
- No broken formatting

### Pass/Fail Criteria:
- **Pass:** All existing stages work as before
- **Fail:** Any stage broken by new changes

---

## Platform-Specific Tests

### MacOS ARM (M1/M2/M3)
1. Check sidebar shows "🍎 MacOS ARM Detected"
2. Try Chrome - should work with ARM-specific settings
3. Try Firefox - should work well (recommended)

### MacOS Intel
1. Both Chrome and Firefox should work
2. No special platform warnings

### Linux/Windows
1. Chrome should be default recommendation
2. Both browsers should work

---

## Quick Smoke Test (5 minutes)

If short on time, run this minimal test:

1. ✅ Start app
2. ✅ Enter research request: "AI healthcare 2025"
3. ✅ Complete Stage 1-2
4. ✅ Check Gap Analysis (Stage 3) - queries look specific?
5. ✅ Run Web Research (Stage 4)
6. ✅ Check analytics expander - metrics showing?
7. ✅ Check for `extracted_content` in terminal output
8. ✅ Verify blog post (Stage 5) has sources

**Pass if:** All checkpoints pass
**Fail if:** Any critical errors or missing features

---

## Comprehensive Test (30 minutes)

For thorough testing:

1. Run Test 1-5 in sequence (core features)
2. Run Test 6 (all search methods)
3. Run Test 8 (error handling)
4. Check performance benchmarks
5. Run regression tests
6. Document any issues found

---

## Known Limitations (Not Bugs)

These are expected behaviors:

1. **Some content extraction fails** - Normal (paywalls, anti-scraping)
2. **Not all queries succeed** - Normal (niche topics, limited content)
3. **Extraction adds time** - Expected (2-3s per page is worth it)
4. **DuckDuckGo rate limiting** - Known limitation of free API
5. **Some sites return snippets only** - Normal (anti-scraping measures)

---

## Bug Report Template

If you find issues:

```
**Test:** [Which test from above]
**Expected:** [What should happen]
**Actual:** [What actually happened]
**Steps:**
1. ...
2. ...

**Environment:**
- OS: [MacOS/Linux/Windows]
- Search Method: [Selenium/DuckDuckGo]
- Browser: [Chrome/Firefox] (if Selenium)
- Python Version: [version]

**Logs/Errors:**
[Paste relevant error messages]

**Analytics at failure:**
- Queries executed: X
- Success rate: Y%
- Content extracted: Z
```

---

## Success Criteria Summary

**Minimum Viable (All must pass):**
- ✅ App starts without errors
- ✅ Gap analysis generates specific queries
- ✅ Web research completes
- ✅ Analytics dashboard displays
- ✅ Some content extraction succeeds (>50%)
- ✅ No crashes on errors

**Optimal (Target):**
- ✅ All minimum viable tests pass
- ✅ Success rate >70%
- ✅ Content extraction >60%
- ✅ All search methods work
- ✅ Performance within benchmarks
- ✅ Blog quality visibly improved

---

## Post-Testing

After testing:

1. ✅ Document any issues found
2. ✅ Note success rates achieved
3. ✅ Identify any edge cases
4. ✅ Test with different research topics
5. ✅ Verify improvements over baseline

---

## Next Steps After Testing

If tests pass:
- Deploy for real usage
- Monitor analytics in production
- Gather user feedback on quality improvement

If tests fail:
- Document specific failures
- Check error logs
- Review implementation against IMPROVEMENTS_SUMMARY.md
- Fix issues and retest
