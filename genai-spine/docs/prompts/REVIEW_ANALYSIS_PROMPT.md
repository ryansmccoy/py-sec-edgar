# Review Analysis Prompt Template

**Slug:** `review-analysis`
**Category:** Quality Assurance
**Version:** 1.0
**Created:** 2026-01-31

---

## Purpose

A structured prompt for having one AI model review and critique work produced by another AI model. Designed to identify weaknesses, edge cases, and improvements while generating actionable feedback.

---

## System Prompt

```
You are a senior technical reviewer with expertise in software architecture,
code quality, and best practices. Your role is to critically review technical
artifacts (documentation, code, architecture decisions) created by another
AI assistant.

Your review style:
- Be thorough but constructive
- Focus on actionable improvements
- Identify specific edge cases and corner cases
- Consider security, performance, and maintainability
- Reference industry best practices when relevant
- Be direct about concerns, but not dismissive

You will produce a structured analysis followed by a prompt that can be
sent back to the original AI assistant to implement improvements.
```

---

## User Prompt Template

```
I need you to review technical artifacts created by {{primary_model}} for
a feature called "{{feature_name}}".

## Context
{{context_description}}

## Artifacts to Review
{{#each artifacts}}
### {{this.name}}
```{{this.format}}
{{this.content}}
```
{{/each}}

## Review Instructions

Please analyze these materials and provide:

### 1. Executive Summary
A 2-3 sentence overview of the implementation quality.

### 2. Strengths (What's Done Well)
List the positive aspects of this implementation that should be preserved.

### 3. Weaknesses & Concerns
Identify issues, risks, or areas needing improvement. Categorize by severity:
- 🔴 **Critical**: Must fix before production
- 🟡 **Important**: Should address soon
- 🟢 **Minor**: Nice to have improvements

### 4. Edge Cases & Corner Cases
List specific scenarios that may not be handled correctly:
- Input edge cases
- Error conditions
- Concurrency issues
- Resource limits
- Integration boundaries

### 5. Best Practice Recommendations
Suggest improvements based on industry standards and patterns.

### 6. Questions for Clarification
Things that are unclear or need more information.

### 7. Improvement Prompt
Generate a detailed prompt I can send back to {{primary_model}} that:
- Summarizes the key findings
- Lists specific improvements to make
- Includes the edge cases to address
- Requests updated documentation/tests

Format the prompt so it can be directly copy-pasted.
```

---

## Example Usage

### Input

```json
{
    "primary_model": "Claude Opus 4.5",
    "feature_name": "Streaming Chat Completions",
    "context_description": "Adding SSE streaming support to the GenAI Spine API",
    "artifacts": [
        {
            "name": "Architecture Decision",
            "format": "markdown",
            "content": "## Streaming Implementation\n\nWe'll use Server-Sent Events (SSE)..."
        },
        {
            "name": "API Endpoint",
            "format": "python",
            "content": "@router.post('/v1/chat/completions/stream')..."
        }
    ]
}
```

### Expected Output Structure

```markdown
## Executive Summary
The streaming implementation follows a reasonable approach using SSE, but lacks
error recovery mechanisms and doesn't address connection timeout scenarios.

## Strengths
- Clean SSE implementation using standard patterns
- Good separation between streaming and non-streaming endpoints
- Proper content-type headers for SSE

## Weaknesses & Concerns

### 🔴 Critical
- **No connection timeout handling**: Long-running streams could hang indefinitely
- **Missing error propagation**: Upstream provider errors not sent to client

### 🟡 Important
- **No heartbeat/keepalive**: Proxies may close idle connections
- **Memory accumulation**: Full response stored in memory during stream

### 🟢 Minor
- **No compression**: Could reduce bandwidth for large responses
- **Missing metrics**: No tracking of streaming vs non-streaming usage

## Edge Cases & Corner Cases
1. What happens if client disconnects mid-stream?
2. How are rate limit errors from providers handled during stream?
3. What if the model returns an empty stream?
4. How is partial token delivery handled (incomplete UTF-8)?
5. Maximum stream duration before forced close?

## Best Practice Recommendations
1. Implement exponential backoff for provider reconnection
2. Add periodic heartbeat events (every 15s)
3. Set maximum stream duration (5 minutes suggested)
4. Use chunked memory handling for large responses
5. Add `retry:` field in SSE for client reconnection hints

## Questions for Clarification
1. What's the expected maximum response size for streaming?
2. Should we support stream cancellation from client?
3. Are there multiple provider streams to merge?

## Improvement Prompt

---
**Prompt for Claude Opus 4.5:**

A technical reviewer has analyzed our Streaming Chat Completions implementation
and identified several improvements needed.

**Critical Issues to Address:**

1. **Connection Timeout Handling**
   - Add configurable timeout (default 5 minutes)
   - Implement graceful stream termination on timeout
   - Send error event before closing

2. **Error Propagation**
   - Catch provider errors during streaming
   - Send SSE error event: `event: error\ndata: {"message": "...", "code": "..."}`
   - Clean up resources on error

**Important Improvements:**

3. **Add Keepalive/Heartbeat**
   - Send comment event every 15 seconds: `: heartbeat`
   - Prevents proxy/load balancer timeouts

4. **Memory Management**
   - Don't accumulate full response in memory
   - Stream-through processing pattern

**Edge Cases to Handle:**

5. Client disconnect during stream
6. Rate limit errors mid-stream
7. Empty response stream
8. Incomplete UTF-8 sequences

**Please:**
- Update the streaming endpoint implementation
- Add unit tests for each edge case
- Update API documentation with error events
- Add streaming-specific metrics

---
```

---

## Variables Reference

| Variable | Type | Description |
|----------|------|-------------|
| `primary_model` | string | Name of the AI that created the artifacts |
| `feature_name` | string | Name of the feature being reviewed |
| `context_description` | string | Background context for the reviewer |
| `artifacts` | array | List of documents/code to review |
| `artifacts[].name` | string | Display name of the artifact |
| `artifacts[].format` | string | Format for syntax highlighting |
| `artifacts[].content` | string | The actual content to review |

---

## Variations

### Quick Review (Lightweight)

For faster reviews with less detail:

```
Review this {{artifact_type}} and identify:
1. Top 3 concerns
2. Top 3 edge cases
3. One-paragraph improvement summary

{{content}}
```

### Security-Focused Review

For security-sensitive code:

```
Perform a security review of this implementation. Focus on:
- Authentication/authorization gaps
- Input validation issues
- Injection vulnerabilities
- Data exposure risks
- Cryptographic weaknesses

{{content}}
```

### Architecture Review

For high-level design:

```
Review this architecture for:
- Scalability concerns
- Single points of failure
- Integration complexity
- Operational considerations
- Cost implications

{{content}}
```

---

## Related Documents

- [MULTI_MODEL_REVIEW_WORKFLOW.md](../features/MULTI_MODEL_REVIEW_WORKFLOW.md) - The workflow this prompt supports
- [GENAI_ADMIN_UI.md](../features/GENAI_ADMIN_UI.md) - UI for managing prompts
