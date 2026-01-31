# Alignment Status

> Current alignment state across all review dimensions.

**Last Updated:** 2025-01-31

---

## Quick Status

| Dimension | Status | Last Review | Next Review |
|-----------|--------|-------------|-------------|
| Documentation | 🟡 Needs Review | — | ASAP |
| Testing | 🟡 Needs Review | — | ASAP |
| Architecture | 🟡 Needs Review | — | ASAP |
| Code Conventions | 🟡 Needs Review | — | ASAP |
| Guardrails | 🟡 Needs Review | — | ASAP |
| TODOs | 🟡 Needs Review | — | ASAP |

**Legend:**
- ✅ Aligned — Passes all checks
- 🟡 Needs Review — Not yet reviewed
- 🟠 Attention Needed — Issues found, plan created
- 🔴 Critical — Blocking issues

---

## Documentation

- **Status:** 🟡 Needs Review
- **Last Review:** Not yet reviewed
- **Issues:** Unknown
- **Plan:** Run `prompts/DOCUMENTATION_REVIEW.md`

## Testing

- **Status:** 🟡 Needs Review
- **Coverage:** Unknown
- **Last Review:** Not yet reviewed
- **Plan:** Run `prompts/TESTING_REVIEW.md`

## Architecture

- **Status:** 🟡 Needs Review
- **Layer Violations:** Unknown
- **Last Review:** Not yet reviewed
- **Plan:** Run `prompts/ARCHITECTURE_REVIEW.md`

## Code Conventions

- **Status:** 🟡 Needs Review
- **Ruff:** Unknown
- **Mypy:** Unknown
- **Last Review:** Not yet reviewed
- **Plan:** Run `prompts/CODE_CONVENTIONS_REVIEW.md`

## Guardrails

- **Status:** 🟡 Needs Review
- **Coverage:** Unknown
- **Last Security Review:** Not yet reviewed
- **Plan:** Run `prompts/GUARDRAILS_REVIEW.md`

## TODOs

- **Status:** 🟡 Needs Review
- **Total TODOs:** Unknown
- **Stale TODOs:** Unknown
- **Last Review:** Not yet reviewed
- **Plan:** Run `prompts/TODO_REVIEW.md`

---

## Recent Activity

| Date | Dimension | Action | Result |
|------|-----------|--------|--------|
| 2025-01-31 | All | Initial setup | Alignment system created |

---

## How to Update

1. Run the relevant prompt from `prompts/`
2. If issues found, create plan in `alignment/plans/`
3. Fix issues
4. Move plan to `alignment/completed/`
5. Update this status file

---

## Scheduled Reviews

| Frequency | Dimensions |
|-----------|------------|
| Per PR | Testing, Architecture, Conventions |
| Weekly | Documentation, TODOs |
| Monthly | Guardrails |
| Before Release | All dimensions + Changelog |
