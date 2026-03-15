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

