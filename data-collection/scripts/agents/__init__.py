"""
Agents package - LLM-based multi-agent system for financial statement parsing.

Contains:
- llm_agents: Auditor, Finalizer, Discoverer agents using Ollama/langchain
- setup_ollama: Setup script for Ollama models
"""

from agents.llm_agents import (
    AgentOrchestrator,
    AgentDecision,
    DiscoveryResult,
    SumRowValidation,
    DateColumnValidation,
    RowClassification,
    check_ollama_available,
    list_ollama_models,
)
