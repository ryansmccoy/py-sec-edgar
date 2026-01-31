# Multi-Model Review Workflow

**Status:** Active Workflow
**Created:** 2026-01-31
**Category:** Productivity / Quality Assurance

---

## Overview

A systematic approach to improving AI-generated outputs by using multiple models as "reviewers" of each other's work. This creates a checks-and-balances system where one model (e.g., ChatGPT-4) reviews and critiques work produced by another model (e.g., Claude Opus 4.5), identifying edge cases, improvements, and potential issues.

---

## The Problem

When working with a single AI model on complex features:
- The model may have blind spots or biases
- Edge cases might be missed
- Best practices specific to one model's training may be overlooked
- No external validation of generated solutions

**Solution:** Use multiple models as a review committee, each providing unique perspectives.

---

## Workflow Steps

### Step 1: Initial Implementation (Primary Model)

Use your primary model (e.g., Claude Opus 4.5) to:
- Design architecture
- Write implementation code
- Generate documentation
- Create test cases

**Output:** Working implementation + documentation

### Step 2: Prepare Review Package

Gather artifacts for review:
```
review_package/
├── architecture.md       # High-level design
├── implementation.md     # Key code decisions
├── api_spec.md          # API contracts
├── test_coverage.md     # Test approach
└── open_questions.md    # Areas of uncertainty
```

### Step 3: Cross-Model Review (Secondary Model)

Send to secondary model (e.g., ChatGPT-4) with the **Review Analysis Prompt**:

```markdown
I need you to act as a senior technical reviewer. I'm sharing documentation
and implementation details created by another AI assistant (Claude Opus 4.5).

Your task:
1. Review the attached materials critically
2. Identify strengths, weaknesses, and blind spots
3. Find edge cases or corner cases that may have been missed
4. Suggest improvements based on best practices
5. Generate a structured prompt I can send back to the original assistant

Materials attached:
- [architecture.md]
- [implementation.md]
- [api_spec.md]
```

### Step 4: Structured Analysis Output

The reviewer model produces:

```markdown
## Review Analysis

### Strengths
- Clean separation of concerns
- Good error handling patterns
- Comprehensive API coverage

### Weaknesses / Concerns
- Missing retry logic for network failures
- No rate limiting consideration
- Potential memory leak in streaming handler

### Edge Cases Identified
1. What happens when model returns empty response?
2. How is partial streaming failure handled?
3. Concurrent request limits not addressed

### Recommended Improvements
1. Add exponential backoff for retries
2. Implement circuit breaker pattern
3. Add request timeout configuration

### Prompt for Primary Model
[Generated prompt to send back to Claude Opus]
```

### Step 5: Implementation Refinement

Send the generated prompt back to the primary model:

```markdown
A technical reviewer has analyzed our implementation and identified
the following improvements needed:

[Paste reviewer's findings]

Please:
1. Address each concern raised
2. Implement the suggested improvements
3. Add tests for the identified edge cases
4. Update documentation to reflect changes
```

### Step 6: Iterate

Repeat steps 2-5 until:
- Both models agree on the approach
- All critical edge cases are addressed
- Implementation meets quality standards

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MULTI-MODEL REVIEW WORKFLOW                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐                          ┌──────────────┐            │
│  │ Claude Opus  │                          │  ChatGPT-4   │            │
│  │   4.5        │                          │  (Reviewer)  │            │
│  │  (Primary)   │                          │              │            │
│  └──────┬───────┘                          └──────┬───────┘            │
│         │                                         │                    │
│         │ 1. Generate                             │                    │
│         │    Implementation                       │                    │
│         ▼                                         │                    │
│  ┌──────────────┐                                │                    │
│  │   Artifacts  │────────────────────────────────┤                    │
│  │  - arch.md   │  2. Send for Review            │                    │
│  │  - impl.md   │                                │                    │
│  │  - tests.md  │                                ▼                    │
│  └──────────────┘                         ┌──────────────┐            │
│         ▲                                 │   Analysis   │            │
│         │                                 │  - Strengths │            │
│         │                                 │  - Weaknesses│            │
│         │                                 │  - Edge Cases│            │
│         │  4. Implement                   │  - Prompt    │            │
│         │     Improvements                └──────┬───────┘            │
│         │                                        │                    │
│         │                                        │ 3. Return          │
│         └────────────────────────────────────────┘    Analysis        │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    ITERATE UNTIL CONSENSUS                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Benefits

| Benefit | Description |
|---------|-------------|
| **Diverse Perspectives** | Different models have different training data and approaches |
| **Edge Case Discovery** | Fresh eyes catch cases the original model missed |
| **Best Practice Validation** | Cross-check against multiple knowledge bases |
| **Reduced Blind Spots** | Compensate for individual model weaknesses |
| **Documentation Quality** | Forces clear documentation for handoff |
| **Iterative Refinement** | Progressive improvement through cycles |

---

## When to Use This Workflow

**Recommended for:**
- Complex feature implementations
- Architecture decisions
- Security-sensitive code
- Public API design
- Critical business logic
- Production-ready releases

**Not necessary for:**
- Simple bug fixes
- Minor documentation updates
- Exploratory prototypes
- Internal tooling

---

## Model Pairing Strategies

| Primary Model | Reviewer Model | Best For |
|---------------|----------------|----------|
| Claude Opus | GPT-4 | Complex systems, architecture |
| GPT-4 | Claude Opus | Different perspective validation |
| Claude Opus | Claude Sonnet | Cost-effective quick reviews |
| GPT-4 | GPT-4-turbo | Fast iteration cycles |
| Any | Gemini 1.5 Pro | Long context review |

---

## Integration with GenAI Spine

### Current State (Manual)
1. Copy artifacts to clipboard
2. Paste into ChatGPT/Claude web UI
3. Copy review back
4. Paste into primary model

### Future State (Automated)

GenAI Spine could automate this workflow:

```python
# Proposed API
POST /v1/multi-model-review
{
    "primary_model": "claude-3-opus",
    "reviewer_model": "gpt-4",
    "artifacts": {
        "architecture": "...",
        "implementation": "...",
        "tests": "..."
    },
    "review_prompt": "review-analysis",  # Use saved prompt
    "auto_iterate": true,
    "max_iterations": 3
}
```

### Required GenAI Spine Features

| Feature | Status | Description |
|---------|--------|-------------|
| Multi-provider support | ✅ Done | Can call OpenAI and Anthropic |
| Chat sessions | 🔴 Needed | Persist conversation history |
| Review prompt template | 🔴 Needed | Standardized review prompts |
| Orchestration endpoint | 🔴 Needed | Coordinate multi-model calls |
| Diff/comparison view | 🔴 Needed | Show changes between iterations |

---

## Prompt Templates for Review Workflow

See: [../prompts/REVIEW_ANALYSIS_PROMPT.md](../prompts/REVIEW_ANALYSIS_PROMPT.md)

---

## Success Metrics

Track the effectiveness of this workflow:

| Metric | Target |
|--------|--------|
| Edge cases caught by reviewer | >3 per major feature |
| Iterations before consensus | 2-3 average |
| Post-release bugs from reviewed code | <50% vs unreviewed |
| Developer confidence score | High (subjective) |

---

## Related Documents

- [GENAI_ADMIN_UI.md](GENAI_ADMIN_UI.md) - Admin interface for managing this workflow
- [REVIEW_ANALYSIS_PROMPT.md](../prompts/REVIEW_ANALYSIS_PROMPT.md) - The review prompt template
- [../TODO.md](../../TODO.md) - Implementation roadmap
