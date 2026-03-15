# LLM Agent System - Comprehensive Workflow Documentation

## Overview

The financial data pipeline uses a multi-agent LLM system to make dynamic decisions that were previously hardcoded or error-prone. This document explains when each agent is called, what it does, and expected outcomes.

---

## Agent Architecture

### 6 Specialized Agents

1. **Auditor** - Resolves ambiguous pattern matches
2. **Finalizer** - Validates economic rationality of matches
3. **Discoverer** - Finds company-specific tags for missing items
4. **SumRowValidator** - Determines if rows are sum/total rows
5. **DateColumnValidator** - Validates fiscal period date columns
6. **RowClassifier** - Classifies unmapped rows

---

## Configuration (PipelineConfig)

### Agent Thresholds (Lowered for More Dynamic Usage)

```python
llm_ambiguity_threshold: 15.0       # Was 5.0 - Call agent when top 2 candidates within 15 points
llm_low_confidence_threshold: 40.0  # Was 25.0 - Call agent when best score < 40
```

**Why lowered?** To trigger agents more often, making the system more dynamic and less reliant on hardcoded rules.

### LLM Configuration

```python
llm_enabled: True
llm_model: "llama3.2"              # Primary model
llm_fallback_model: "mistral"      # Fallback if primary fails
llm_analysis_model: "deepseek-r1"  # For numerical analysis (Discoverer)
llm_base_url: "http://localhost:11434"
```

---

## Agent 1: AUDITOR

### When Called
- In `pipeline._select_best_mappings()` during Step 5
- Triggered when:
  - **Ambiguity**: Top 2 candidates have scores within 15 points of each other
  - **Low confidence**: Best candidate score < 40

### Input Context
```python
{
    'row_idx': 'us-gaap_RevenueFromContractWithCustomer...',
    'human_label': 'Total revenues',
    'candidates': [Top 3 MatchCandidate objects],
    'row_values': {'2024': 833000000, '2023': 795000000},
    'surrounding_rows': [Context rows],
    'temporal_info': {Cross-year validation results},
    'sum_check_info': {Summation verification results}
}
```

### What It Does
1. Analyzes GAAP tag semantics
2. Compares numerical values across candidates
3. Considers cross-year consistency
4. Evaluates summation logic
5. Returns recommended fact + confidence + reasoning

### Output
```python
AgentDecision(
    selected_fact='Total revenue',
    confidence=0.95,
    reasoning='High regex score and exact GAAP tag match...',
    agent_name='Auditor'
)
```

### Terminal Logging
```
INFO:agents.llm_agents:[Agent:Auditor] Analyzing 'us-gaap_Revenue...' with 3 candidates
INFO:agents.llm_agents:[Agent:Auditor]   Candidate 1: 'Total revenue' (score=60.0, type=GAAP)
INFO:agents.llm_agents:[Agent:Auditor] Calling model 'llama3.2'...
INFO:agents.llm_agents:[Agent:Auditor] Response received from 'llama3.2' (4.4s, 369 chars)
INFO:agents.llm_agents:[Agent:Auditor] Decision: 'Total revenue' (conf=0.95) - ...
```

### File Logging
Full prompt and response written to `agents/logs/llm_interactions.jsonl`

---

## Agent 2: FINALIZER

### When Called
- After Auditor, only if Auditor confidence < 0.9
- Acts as a second opinion/economic sanity check

### Input Context
```python
{
    'auditor_decision': AgentDecision(...),
    'row_idx': '...',
    'human_label': '...',
    'row_values': {...},
    'historical_trend': {'2024': 833M, '2023': 795M, '2022': 745M, ...}
}
```

### What It Does
1. Reviews Auditor's recommendation
2. Checks if 10-year trend makes economic sense
3. Validates that Revenue grows reasonably
4. Confirms Net Income is proportional to Revenue
5. Can override Auditor if economically irrational

### Output
```python
AgentDecision(
    selected_fact='Total revenue',  # Confirmed or overridden
    confidence=0.92,
    reasoning='Trend is economically sound...',
    agent_name='Finalizer'
)
```

### Terminal Logging
```
INFO:agents.llm_agents:[Agent] Auditor confidence 0.85 < 0.9, escalating to Finalizer
INFO:agents.llm_agents:[Agent:Finalizer] Reviewing Auditor decision for '...'
INFO:agents.llm_agents:[Agent:Finalizer] CONFIRMED Auditor: 'Total revenue' (conf=0.92)
```

Or if overriding:
```
INFO:agents.llm_agents:[Agent:Finalizer] OVERRODE Auditor: 'SG&A' -> 'Total operating expense' (conf=0.88)
```

---

## Agent 3: DISCOVERER

### When Called
- In `pipeline.run()` Step 6
- After all regex matching is complete
- Only when expected facts are still missing

### Input Context
```python
{
    'unmatched_rows': [
        {
            'idx': 'tsla_RestructuringAndOther',
            'human_label': 'Restructuring and other',
            'camelcase_words': 'Restructuring And Other',
            'values': {'2024': -50M, '2023': -35M}
        },
        ...
    ],
    'expected_items': ['Total revenue', 'Operating income'],
    'statement_type': 'income_statement'
}
```

### What It Does
1. Examines unmatched rows in batches of 5
2. Looks for company-specific tags (e.g., `tsla_*`, `aapl_*`)
3. Uses CamelCase decomposition and human labels
4. Considers numerical magnitudes (billions = revenue-level)
5. Suggests which expected items these rows might represent

### Output
```python
[
    DiscoveryResult(
        row_idx='tsla_RestructuringAndOther',
        suggested_fact='Restructuring charges',
        confidence=0.75,
        reasoning='CamelCase and label indicate restructuring expense...'
    ),
    ...
]
```

### Terminal Logging
```
INFO:agents.llm_agents:[Agent:Discoverer] Searching 15 unmatched rows for 2 missing items
INFO:agents.llm_agents:[Agent:Discoverer] Batch 1/3: ['tsla_Restructuring...', ...]
INFO:agents.llm_agents:[Agent:Discoverer] Found: 'tsla_Restructuring...' -> 'Restructuring charges' (conf=0.75)
INFO:agents.llm_agents:[Agent:Discoverer] Complete: 2 discoveries from 15 rows
```

---

## Agent 4: SUMROWVALIDATOR (NEW)

### When Called
- **Future integration**: In `Filling.py` when processing HTML tables
- Can replace hardcoded HTML class checking (`reu`, `rou`)

### Current Use Case
HTML classes `reu`/`rou` indicate sum rows, but they're not always reliable. Agent provides dynamic validation.

### Input Context
```python
{
    'row_idx': 'us-gaap_OperatingExpenses',
    'human_label': 'Total operating expenses',
    'row_values': {'2024': -362M, '2023': -346M},
    'html_class': 'reu',
    'potential_components': ['us-gaap_RnD', 'us-gaap_SGA', ...]
}
```

### What It Does
1. Examines row label for "Total", "Net", summation keywords
2. Checks if HTML class indicates sum row
3. Analyzes if numerical value ≈ sum of components
4. Returns whether it's a sum row + confidence

### Output
```python
SumRowValidation(
    row_idx='us-gaap_OperatingExpenses',
    is_sum_row=True,
    confidence=0.90,
    reasoning='Label contains "Total" and value matches sum of components',
    component_rows=['us-gaap_RnD', 'us-gaap_SGA', ...]
)
```

### Terminal Logging
```
INFO:agents.llm_agents:[Agent:SumRowValidator] Validating 'us-gaap_OperatingExpenses' (label='Total operating expenses')
INFO:agents.llm_agents:[Agent:SumRowValidator] Result: is_sum=True (conf=0.90)
```

---

## Agent 5: DATECOLUMNVALIDATOR (NEW)

### When Called
- **Future integration**: In `Filling.py` when extracting date columns from HTML tables
- Validates which columns are fiscal period dates vs. metadata/ratio columns

### Current Use Case
Some filings have columns like "Shares", "Per Share", "12 Months Ended" mixed with actual date columns.

### Input Context
```python
{
    'all_columns': ['2024-09-28', '2023-09-30', 'Shares', '12 Months Ended 2024-09-28'],
    'sample_values': {
        '2024-09-28': [833000000, -400000000, 433000000],
        'Shares': [172000000, 172000000, 172000000],
        ...
    }
}
```

### What It Does
1. Identifies columns matching date format (YYYY-MM-DD)
2. Excludes columns with descriptive text or ratios
3. Detects duplicate/redundant date columns
4. Returns selected fiscal period dates

### Output
```python
DateColumnValidation(
    selected_columns=['2024-09-28', '2023-09-30', '2022-09-24'],
    rejected_columns=['Shares', '12 Months Ended 2024-09-28'],
    confidence=0.92,
    reasoning='Selected columns match date format and contain financial values. Excluded metadata columns.'
)
```

### Terminal Logging
```
INFO:agents.llm_agents:[Agent:DateColumnValidator] Validating 4 columns
INFO:agents.llm_agents:[Agent:DateColumnValidator] Selected 3/4 columns (conf=0.92)
```

---

## Agent 6: ROWCLASSIFIER (NEW)

### When Called
- **Future integration**: Post-pipeline analysis of unmapped rows
- Identifies important financial concepts that regex missed

### Current Use Case
After pipeline completes, some rows remain unmapped. Agent classifies them to determine if they're important.

### Input Context
```python
{
    'row_idx': 'aapl_ServicesRevenue',
    'human_label': 'Services',
    'row_values': {'2024': 85M, '2023': 78M},
    'camelcase_words': 'Services Revenue'
}
```

### What It Does
1. Examines GAAP tag and CamelCase decomposition
2. Considers human label and value magnitude
3. Determines if row represents a standard concept
4. Classifies as relevant/irrelevant
5. Suggests which financial concept it represents

### Output
```python
RowClassification(
    row_idx='aapl_ServicesRevenue',
    financial_concept='Services revenue',
    is_relevant=True,
    confidence=0.85,
    reasoning='CamelCase and label clearly indicate services revenue component'
)
```

### Terminal Logging
```
INFO:agents.llm_agents:[Agent:RowClassifier] Classifying 'aapl_ServicesRevenue'
INFO:agents.llm_agents:[Agent:RowClassifier] Classified as 'Services revenue' (conf=0.85)
```

---

## Complete Pipeline Flow with Agents

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Create Empty Mapped DataFrame                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Generate Regex Candidates                              │
│ - HybridMatcher finds potential MapFacts for each row          │
│ - Scores based on GAAP/IFRS/Human patterns                     │
│ - Penalizes dimensional rows (Revenue::, D1:)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Temporal Cross-Year Validation                         │
│ - Compares values to historical filings                        │
│ - Boosts score if matches previous year's mapping              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Summation Verification                                 │
│ - Checks if sum rows actually sum to components                │
│ - Adjusts scores based on sum accuracy                         │
│ - FUTURE: Use SumRowValidator agent here                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Select Best Mappings + LLM Tie-Breaking               │
│ - For each row, pick best candidate                            │
│ - IF ambiguous (gap < 15.0) OR low confidence (< 40.0):        │
│   ├─► AGENT 1: AUDITOR                                         │
│   │   Analyzes top 3 candidates + context                      │
│   │   Returns: recommended fact + confidence                   │
│   └─► IF Auditor confidence < 0.9:                             │
│       └─► AGENT 2: FINALIZER                                   │
│           Validates economic rationality                        │
│           Returns: confirmed or overridden decision             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Discovery of Missing Items                             │
│ - Check which expected facts are still missing                 │
│ - IF missing AND discovery_enabled:                            │
│   └─► AGENT 3: DISCOVERER                                      │
│       Examines unmatched rows for company-specific tags        │
│       Returns: suggested mappings for missing items            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Post-Processing (FUTURE Integration)                           │
│ - AGENT 4: SumRowValidator - validate sum rows dynamically     │
│ - AGENT 5: DateColumnValidator - validate date columns         │
│ - AGENT 6: RowClassifier - classify remaining unmapped rows    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Logging System

### Terminal Logs (INFO level, visible in uvicorn)

All agent activities logged with `[Agent:...]` prefix:
- Agent invocations
- Model calls and response times
- Decisions and reasoning
- Pipeline LLM tie-break triggers

### File Logs (JSONL format)

Full prompt/response pairs written to: `agents/logs/llm_interactions.jsonl`

Each line is a JSON record:
```json
{
  "timestamp": "2026-02-16T11:35:00",
  "agent": "Auditor",
  "model": "llama3.2",
  "system_prompt": "You are a Senior Financial Data Auditor...",
  "user_prompt": "## Row to Match\n- **Raw GAAP Tag**: ...",
  "response": "{\"selected_fact\": \"Total revenue\", ...}",
  "duration_seconds": 4.41,
  "error": null
}
```

### Why Agents Weren't Called in RBBN Example

The RBBN run had `DISABLE_LLM=1` OR regex matches were highly confident:
- `us-gaap_RevenueFromContractWithCustomer...` → score 50+ (GAAP exact match)
- No ambiguity (no close runner-up candidates)
- Score > 40 (above low_confidence_threshold)

**With new thresholds (15.0, 40.0)**, agents will trigger more often.

---

## Testing Agent Triggers

### Verify Agents Are Called

```bash
cd data-collection/scripts
python3 main.py --ticker RBBN --years 3

# Look for logs like:
# INFO:pipeline:[Pipeline] LLM tie-break needed for '...'
# INFO:agents.llm_agents:[Agent:Auditor] Analyzing '...'
# INFO:agents.llm_agents:[Agent:Discoverer] Searching ...
```

### Check LLM Log File

```bash
tail -f agents/logs/llm_interactions.jsonl | jq .
```

---

## Future Integration Points

### 1. Integrate SumRowValidator in Filling.py
Replace:
```python
if row_class == ['reu'] or row_class == ['rou']:
    rows_that_are_sum.append(row_title)
```

With:
```python
if agent_orchestrator:
    validation = agent_orchestrator.validate_sum_row(
        row_idx=row_title,
        human_label=row_text,
        row_values=row_values_dict,
        html_class=row_class,
        potential_components=previous_rows
    )
    if validation.is_sum_row and validation.confidence > 0.7:
        rows_that_are_sum.append(row_title)
```

### 2. Integrate DateColumnValidator in Filling.py
Replace regex-based date column selection with agent validation.

### 3. Integrate RowClassifier Post-Pipeline
After pipeline completes, run RowClassifier on all unmapped rows to identify missed concepts.

---

## Performance Considerations

- **Average agent call**: 3-6 seconds (depends on model)
- **Parallelization**: Agents currently run sequentially
- **Caching**: LLM responses not cached (each call hits Ollama)
- **Optimization**: Could batch similar rows to reduce calls

---

## Troubleshooting

### Agents Not Being Called

1. Check if `llm_enabled=True` in PipelineConfig
2. Check if `DISABLE_LLM` env var is set
3. Verify Ollama is running: `check_ollama_available()`
4. Check thresholds - scores may be too confident

### LLM Responses Failing to Parse

- Check `agents/logs/llm_interactions.jsonl` for raw responses
- LLM may not be following JSON format
- Try different model (mistral fallback)
- Adjust temperature (lower = more deterministic)

### Slow Performance

- Reduce `llm_ambiguity_threshold` to trigger agents less
- Use faster model (mistral instead of llama3)
- Consider caching LLM responses
- Batch similar decisions

---

## Summary

The agent system makes the financial data pipeline **dynamic and adaptive** rather than relying on hardcoded rules. By lowering thresholds and adding new agent roles, the system can:

1. **Resolve ambiguity** when regex matching isn't confident
2. **Validate economic rationality** of matches
3. **Discover company-specific tags** that regex can't handle
4. **Validate sum rows** beyond simple HTML class checking
5. **Validate date columns** to exclude metadata
6. **Classify unmapped rows** to catch missed concepts

All agent activity is logged both to terminal (INFO level) and to JSONL files for review.
