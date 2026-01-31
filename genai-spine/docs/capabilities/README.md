# GenAI Spine Capabilities Overview

> Complete matrix of AI capabilities organized by maturity tier.

---

## Tier System

| Tier | Name | Description | Priority |
|------|------|-------------|----------|
| **1** | Basic | Core functionality, MVP requirements | 🔴 Must Have |
| **2** | Intermediate | Enhanced features, common use cases | 🟡 Should Have |
| **3** | Advanced | Complex features, power user needs | 🟢 Nice to Have |
| **4** | Mind-Blowing | Future vision, differentiation | 🔵 Aspirational |

---

## Quick Reference

| Capability | Tier | Status | Domain |
|------------|------|--------|--------|
| Text Completion | 1 | ✅ | Core |
| Text Summarization | 1 | ✅ | Core |
| Classification | 1 | ✅ | Core |
| Entity Extraction (NER) | 1 | ✅ | Core |
| Key Point Extraction | 1 | 🟡 | Core |
| Template Rendering | 1 | ✅ | Core |
| Prompt Management | 1 | ✅ | Core |
| Prompt Versioning | 1 | ✅ | Core |
| Cost Tracking | 1 | 🟡 | Core |
| Provider Abstraction | 1 | ✅ | Core |
| Sentiment Analysis | 2 | 🔴 | Core |
| Question Answering | 2 | 🔴 | Core |
| Content Tagging | 2 | 🔴 | Core |
| Response Caching | 2 | 🔴 | Core |
| RAG (Basic) | 2 | 🔴 | Core |
| Document Comparison | 3 | 🔴 | Core |
| Multi-Doc Synthesis | 3 | 🔴 | Core |
| Chain-of-Thought | 3 | 🔴 | Core |
| RAG (Advanced) | 3 | 🔴 | Core |
| Autonomous Agents | 4 | 🔴 | Core |
| **Financial Capabilities** | | | |
| Earnings Sentiment | 2 | 🔴 | Financial |
| Filing Summarization | 2 | 🔴 | Financial |
| Financial NER | 2 | 🔴 | Financial |
| Risk Factor Extraction | 3 | 🔴 | Financial |
| 10-K Comparison | 3 | 🔴 | Financial |

---

## Detailed Tier Docs

- [TIER_1_BASIC.md](TIER_1_BASIC.md) — 15 core capabilities
- [TIER_2_INTERMEDIATE.md](TIER_2_INTERMEDIATE.md) — 15 enhanced capabilities
- [TIER_3_ADVANCED.md](TIER_3_ADVANCED.md) — 15 advanced capabilities
- [TIER_4_MINDBLOWING.md](TIER_4_MINDBLOWING.md) — 15 future capabilities

---

## Core Infrastructure Capabilities

These aren't "AI capabilities" but essential infrastructure:

| Component | Description | Tier | Status |
|-----------|-------------|------|--------|
| Prompt CRUD | Create, read, update, delete prompts | 1 | ✅ |
| Prompt Versioning | Immutable version history | 1 | ✅ |
| Prompt Variables | Template variable substitution | 1 | ✅ |
| Prompt Library | Built-in prompt templates | 1 | ✅ |
| Provider Registry | Multi-provider support | 1 | ✅ |
| Provider Routing | Intelligent model selection | 2 | 🔴 |
| Provider Fallback | Automatic failover | 2 | 🔴 |
| Cost Calculation | Per-request cost tracking | 1 | 🟡 |
| Cost Budgets | Daily/monthly limits | 2 | 🔴 |
| Response Caching | Cache identical requests | 2 | 🔴 |
| Semantic Caching | Cache similar requests | 3 | 🔴 |
| Vector Storage | Embeddings for RAG | 2 | 🔴 |
| SSE Streaming | Real-time token streaming | 2 | 🔴 |
| Batch Processing | Queue large jobs | 3 | 🔴 |
| A/B Testing | Compare prompt versions | 3 | 🔴 |

---

## Domain Extensions

GenAI Spine is domain-agnostic at its core. Domain-specific capabilities live in extension modules:

| Domain | Location | Description |
|--------|----------|-------------|
| Financial Markets | [domains/financial-markets/](../domains/financial-markets/) | SEC filings, earnings, sentiment |
| (Future) Legal | `domains/legal/` | Contract analysis, compliance |
| (Future) Healthcare | `domains/healthcare/` | Clinical notes, research |
| (Future) News | `domains/news/` | Article processing, bias detection |

See [domains/README.md](../domains/README.md) for extension architecture.
