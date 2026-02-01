# Ecosystem Audit Tools - Complete Guide

## 📊 Overview

We've created a comprehensive suite of analysis tools to slice and dice the codebase in multiple dimensions, identifying technical debt, test coverage gaps, and refactoring opportunities.

---

## 🔧 Tools Available

### 1. **Feature Implementation Matrix** (`scripts/audit_all_projects.py`)
High-level view of what's implemented across all layers.

**Usage:**
```bash
python scripts/audit_all_projects.py
python scripts/audit_all_projects.py --detailed
python scripts/audit_all_projects.py --json exports/ecosystem_audit.json
```

**What it shows:**
- API endpoints, CLI commands, backend services per project
- Frontend pages and components
- Tests and examples count
- Quick gaps: Features present in API but missing from CLI, etc.

**Output:**
| Project | API | CLI | Backend | Frontend | Tests | Examples |
|---------|-----|-----|---------|----------|-------|----------|
| capture-spine | 415r/88f | 73c/15f | 28 | 39p/144c | 65 | 4 |
| entityspine | 13r/1f | - | 8 | - | 23 | 20 |

---

### 2. **Comprehensive Ecosystem Audit** (`scripts/comprehensive_ecosystem_audit.py`)
Multi-dimensional deep dive into every project.

**Usage:**
```bash
python scripts/comprehensive_ecosystem_audit.py --all
python scripts/comprehensive_ecosystem_audit.py --git     # Git status only
python scripts/comprehensive_ecosystem_audit.py --gaps    # Coverage gaps only
python scripts/comprehensive_ecosystem_audit.py --issues  # All issues
python scripts/comprehensive_ecosystem_audit.py --json exports/comprehensive_audit.json
```

**Dimensions analyzed:**
1. **Test Structure** - Unit/integration/e2e breakdown, async tests, mocked tests, fixtures
2. **Git Analysis** - Uncommitted files, recent commits, contributors, staleness
3. **Coverage Gaps** - Source files without corresponding tests (with file→test mapping)
4. **Documentation** - README, docstrings, API docs, guides coverage
5. **Dead Code** - Unused imports, empty files, TODO/FIXME comments
6. **Dependencies** - Installed packages, internal dependencies, version conflicts
7. **Configuration** - pyproject.toml, Docker, CI/CD, pre-commit consistency
8. **Code Quality** - Lines of code, comment ratio, function length, type hints usage

**Sample Output:**
```
ECOSYSTEM HEALTH SUMMARY
Project          Score  Tests  Unit  Integ  E2E  Gaps  Docs%  Issues
----------------------------------------------------------------------
capture-spine    100    620    12    5      0    0     0%     2
entityspine      100    586    11    6      0    103   96%    2
feedspine        100    819    35    1      0    43    96%    2
genai-spine      89     86     7     0      0    28    94%    5
spine-core       63     2      0     0      0    0     0%     5
py_sec_edgar     86     852    22    8      1    0     0%     4
```

**Key Findings:**
- **entityspine**: 103 files without tests (569 functions, 44K lines untested)
- **feedspine**: 43 files without tests (161 functions, 14K lines untested)
- **genai-spine**: 13 uncommitted files, missing CI/CD
- **spine-core**: Only 2 test functions, no pyproject.toml
- **py_sec_edgar**: No commits in 151 days

---

### 3. **Interactive Audit Analyzer** (`scripts/analyze_audit_data.py`)
Load JSON exports and interactively explore the data.

**Usage:**
```bash
# Quick views
python scripts/analyze_audit_data.py --summary
python scripts/analyze_audit_data.py --tests
python scripts/analyze_audit_data.py --gaps
python scripts/analyze_audit_data.py --quality

# Interactive mode (BEST!)
python scripts/analyze_audit_data.py --interactive
```

**Interactive Commands:**
```
> summary          - Overall health summary
> tests            - Test breakdown by project
> test-files       - Test files by type (unit/integration/e2e)
> gaps             - Coverage gaps summary
> gaps-top         - 20 largest untested files
> gaps entityspine - Coverage gaps for specific project
> quality          - Code quality metrics
> complex          - List complex functions (>50 lines)
> git              - Git status summary
> uncommitted      - Uncommitted files
> docs             - Documentation coverage
> undoc entityspine - Undocumented items in project
> dead             - Dead code / TODO analysis
> todos            - All TODO/FIXME comments
> config           - Configuration matrix
> config-missing   - Missing configurations
> issues           - All issues by project
> critical         - Critical issues only
> compare p1 p2    - Side-by-side comparison
> rank score       - Rank by: score, tests, docstrings, typehints, gaps, issues
> help             - Show menu
> quit             - Exit
```

**Example Session:**
```
> gaps-top
TOP 20 LARGEST UNTESTED FILES
Project      File                                       Lines  Funcs  Classes
entityspine  src\entityspine\domain\graph.py           1829   10     10
entityspine  src\entityspine\domain\markets.py         1453   10     10
feedspine    src\feedspine\earnings\service.py         1061   10     10

> compare capture-spine entityspine
PROJECT COMPARISON: capture-spine, entityspine
Metric                capture-spine  entityspine
Score                 100            100
Test Functions        620            586
Coverage Gaps         0              103
Docstring Coverage    0%             96%
```

---

### 4. **Refactoring Opportunities Analyzer** (`scripts/refactoring_opportunities.py`) ⭐ NEW
Identify files, classes, and methods that need refactoring based on size and complexity.

**Usage:**
```bash
# Analyze all projects
python scripts/refactoring_opportunities.py --top 30

# Single project
python scripts/refactoring_opportunities.py --project entityspine --top 20

# Show detailed file structure (classes, methods, lines)
python scripts/refactoring_opportunities.py --project entityspine \
  --file "src\entityspine\stores\sqlite_store.py"

# Export for AI analysis
python scripts/refactoring_opportunities.py --project entityspine \
  --ai-prompt exports/entityspine_refactoring_prompt.md --top 10

# JSON export
python scripts/refactoring_opportunities.py \
  --json exports/ecosystem_refactoring.json
```

**What it detects:**
- **Huge Files** (>1000 lines) - Candidates for module splitting
- **Large Files** (>500 lines) - Consider splitting
- **God Classes** (>30 methods) - SRP violations
- **Huge Classes** (>500 lines) - Extract helper classes
- **Large Classes** (>300 lines) - Review responsibilities
- **Very Long Methods** (>100 lines) - Extract helper methods
- **Long Methods** (>50 lines) - Consider simplification
- **Complex Methods** (cyclomatic complexity >10) - Simplify logic

**Thresholds:**
```python
THRESHOLDS = {
    "large_file": 500,
    "huge_file": 1000,
    "large_class": 300,
    "huge_class": 500,
    "long_method": 50,
    "very_long_method": 100,
    "many_methods": 20,
    "god_class": 30,
    "complex_function": 10,
}
```

**Sample Output:**
```
REFACTORING OPPORTUNITIES SUMMARY
Total opportunities: 229
  High priority:     50
  Medium priority:   179

By type:
  long_method          105
  complex_method        40
  large_file            30
  very_long_function    16
  huge_class            14
  very_long_method      14
  god_class              2

TOP REFACTORING OPPORTUNITIES
1. [!!!] HUGE_FILE: src\entityspine\stores\sqlite_store.py
   Location: entire file
   File has 2144 lines of code
   Metrics: lines=2144, classes=1, functions=0
   Suggestions:
     - Split into multiple modules by responsibility
     - Extract classes into separate files

2. [!!!] GOD_CLASS: src\entityspine\stores\sqlite_store.py
   Location: class SqliteStore (lines 467-2596)
   Class 'SqliteStore' has 92 methods
   Metrics: methods=92, lines=2130, properties=0
   Suggestions:
     - Apply Single Responsibility Principle
     - Extract related methods into separate classes
     - Use composition over inheritance
     - Consider facade or strategy patterns
```

**Detailed File Structure Example:**
```
FILE STRUCTURE: src\entityspine\stores\sqlite_store.py
Lines: 2598 (code: 2144, comments: 114, blank: 340)
Imports: 29
Classes: 1
Functions: 0

CLASS: SqliteStore (lines 467-2596, 2130 lines)
  Methods: 92
    __init__(self, db_path) - 37 lines, complexity 1
    load_sec_json(self, data) - 104 lines, complexity 10 [LONG]
    search_entities(self, query, limit) - 72 lines, complexity 14 [complex]
    _create_security_and_listing(...) - 69 lines [LONG]
    ... and 88 more methods
```

**AI-Friendly Export:**
The `--ai-prompt` flag generates a markdown file with:
- Top N refactoring candidates
- File structure details
- Class/method breakdown with metrics
- Current suggestions
- Formatted for AI to provide specific refactoring strategies

---

## 🎯 Common Workflows

### Workflow 1: Weekly Health Check
```bash
# Generate comprehensive audit
python scripts/comprehensive_ecosystem_audit.py --all \
  --json exports/weekly_audit_$(date +%Y%m%d).json

# Review interactively
python scripts/analyze_audit_data.py -i
> summary
> critical
> uncommitted
```

### Workflow 2: Pre-Release Validation
```bash
# Check all dimensions
python scripts/comprehensive_ecosystem_audit.py --all

# Look for blockers
python scripts/analyze_audit_data.py --issues

# Check uncommitted work
python scripts/analyze_audit_data.py --git
```

### Workflow 3: Identify Refactoring Targets
```bash
# Find largest problems
python scripts/refactoring_opportunities.py --top 20

# Deep dive on specific project
python scripts/refactoring_opportunities.py \
  --project entityspine \
  --ai-prompt exports/entityspine_refactor.md \
  --top 10

# Get detailed class structure
python scripts/refactoring_opportunities.py \
  --project entityspine \
  --file "src\entityspine\stores\sqlite_store.py"
```

### Workflow 4: Test Coverage Improvement
```bash
# Identify untested files
python scripts/analyze_audit_data.py -i
> gaps
> gaps-top
> gaps entityspine

# Get specific file list
python scripts/comprehensive_ecosystem_audit.py \
  --gaps --json exports/gaps.json

# Parse JSON to create test stubs
python -c "
import json
data = json.load(open('exports/comprehensive_audit.json'))
for p in data['projects'].values():
    for gap in p['coverage_gaps']:
        print(f'TODO: Create test for {gap[\"source_file\"]}')
"
```

### Workflow 5: Compare Projects
```bash
python scripts/analyze_audit_data.py -i
> compare entityspine feedspine genai-spine
> rank score
> rank tests
> rank docstrings
```

---

## 📈 Metrics Explained

### Health Score (0-100)
Calculated as:
- Start at 100
- Deduct 20 for each CRITICAL issue
- Deduct 10 for each WARNING
- Deduct 2 for each INFO issue
- Bonus +5 for >50 tests
- Bonus +5 for integration tests
- Bonus +5 for >70% docstrings
- Bonus +5 for CI/CD config
- Bonus +5 for >80% type hints

### Coverage Gap Severity
- **0 gaps** = Excellent (all source files have tests)
- **1-20 gaps** = Good (minor holes)
- **21-50 gaps** = Fair (needs attention)
- **50+ gaps** = Poor (major test debt)

### Refactoring Priority
- **HIGH**: Immediate action needed (huge files, god classes, very long methods)
- **MEDIUM**: Should address soon (large files, long methods, complex methods)
- **LOW**: Monitor (approaching thresholds)

---

## 📂 Export Files

All tools support JSON export for programmatic analysis:

```
exports/
├── ecosystem_audit.json              # Simple feature matrix
├── comprehensive_audit.json          # Full multi-dimensional audit
├── ecosystem_refactoring.json        # All refactoring opportunities
├── entityspine_refactoring.json      # Project-specific refactoring
└── entityspine_refactoring_prompt.md # AI-friendly refactoring guide
```

---

## 🔮 Future Enhancements

Potential additions:
1. **Dependency Graph Analysis** - Visualize inter-project dependencies
2. **Import Analysis** - Detect circular imports, unused modules
3. **API Coverage** - OpenAPI spec vs implementation
4. **Database Migration Coverage** - Alembic/migration analysis
5. **Feature Flag Tracking** - Detect feature flags in code
6. **Security Scan** - Common vulnerability patterns
7. **Performance Hotspots** - Identify slow patterns (O(n²) loops, etc.)
8. **HTML Dashboard** - Visual reports with charts
9. **Trend Analysis** - Track metrics over time
10. **AI Auto-Refactoring** - Generate PR with refactoring suggestions

---

## 🎓 Tips

1. **Run audits weekly** - Track trends over time
2. **Focus on high-priority refactoring** - Don't try to fix everything at once
3. **Use interactive mode** - Much faster than re-running scripts
4. **Export to JSON** - Build custom analysis scripts
5. **AI-prompt files** - Great for getting detailed refactoring suggestions from LLMs
6. **Compare before/after** - Validate that refactoring improved metrics
7. **Automate in CI** - Fail builds if critical issues increase

---

## 📊 Current State (Jan 31, 2026)

### Overall Ecosystem
- **Total Projects**: 6
- **API Routes**: 461
- **CLI Commands**: 73
- **Tests**: 192 files (2,965 test functions)
- **Coverage Gaps**: 174 files (65K lines untested)
- **Refactoring Opportunities**: 229 (50 high priority)

### Top Issues to Address
1. **entityspine/SqliteStore** - 2,144 line file, 92 methods (god class)
2. **entityspine** - 103 source files without tests
3. **feedspine** - 43 source files without tests
4. **genai-spine** - No CI/CD, 13 uncommitted files
5. **spine-core** - Only 2 tests, no pyproject.toml
6. **py_sec_edgar** - No commits in 151 days

### Strengths
- ✅ Strong docstring coverage (96%+ in entityspine, feedspine, genai-spine)
- ✅ High type hint usage (96-100% in some projects)
- ✅ Good test counts (620-852 test functions in main projects)
- ✅ Consistent tooling (ruff linter across all)

---

## 🤖 Example: Using AI for Refactoring

```bash
# Generate AI prompt
python scripts/refactoring_opportunities.py \
  --project entityspine \
  --ai-prompt exports/refactor_sqlite_store.md \
  --top 1

# Send to Claude/GPT
cat exports/refactor_sqlite_store.md | gh copilot suggest
# or paste into Claude/ChatGPT

# AI will suggest:
# - New file structure (split into modules)
# - Classes to extract
# - Patterns to apply (Repository, Strategy, Facade)
# - Step-by-step refactoring plan
```

---

## 📞 Quick Reference

```bash
# Daily health check
python scripts/comprehensive_ecosystem_audit.py

# Find what to work on next
python scripts/refactoring_opportunities.py --top 10

# Interactive exploration
python scripts/analyze_audit_data.py -i

# Full export for analysis
python scripts/comprehensive_ecosystem_audit.py --all \
  --json exports/audit.json
python scripts/refactoring_opportunities.py \
  --json exports/refactor.json
```

---

**Last Updated**: January 31, 2026
**Tools Version**: 1.0
**Audit Coverage**: 6 projects, 174 coverage gaps identified, 229 refactoring opportunities detected
