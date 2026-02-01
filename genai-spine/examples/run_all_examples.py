#!/usr/bin/env python3
"""Run All GenAI Spine Examples.

This script runs all example scripts in sequence to demonstrate
the full capabilities of GenAI Spine.

Usage:
    # Start Docker first
    docker compose up -d
    docker compose exec ollama ollama pull llama3.2:latest

    # Run all examples
    python examples/run_all_examples.py

    # Run specific examples
    python examples/run_all_examples.py --only 1,2,3
    python examples/run_all_examples.py --skip 8,9

Options:
    --only N,N,N    Run only specified example numbers
    --skip N,N,N    Skip specified example numbers
    --quick         Run quick examples only (1, 5, 9, 10)
    --base-url URL  Use custom API URL (default: http://localhost:8100)
"""

import argparse
import subprocess
import sys
from pathlib import Path
import httpx

# Example scripts in order
EXAMPLES = [
    ("01_health_check.py", "Health Check & Service Discovery", False),
    ("02_chat_completion.py", "Chat Completion (OpenAI-Compatible)", True),
    ("03_summarization.py", "Text Summarization", True),
    ("04_entity_extraction.py", "Entity Extraction", True),
    ("05_classification.py", "Content Classification", True),
    ("06_rewrite.py", "Content Rewriting (Message Enrichment)", True),
    ("07_title_inference.py", "Title Inference", True),
    ("08_commit_generation.py", "Commit Message Generation", True),
    ("09_prompt_management.py", "Prompt Management (CRUD)", False),
    ("10_cost_tracking.py", "Cost Tracking & Usage", False),
]

QUICK_EXAMPLES = [1, 5, 9, 10]


def check_service(base_url: str) -> bool:
    """Check if GenAI Spine is running."""
    try:
        response = httpx.get(f"{base_url}/health", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


def run_example(script_path: Path, base_url: str) -> bool:
    """Run a single example script."""
    env = {"BASE_URL": base_url}
    result = subprocess.run(
        [sys.executable, str(script_path)],
        env={**subprocess.os.environ, **env},
        capture_output=False,
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run GenAI Spine examples")
    parser.add_argument("--only", help="Run only these example numbers (comma-separated)")
    parser.add_argument("--skip", help="Skip these example numbers (comma-separated)")
    parser.add_argument("--quick", action="store_true", help="Run quick examples only")
    parser.add_argument("--base-url", default="http://localhost:8100", help="API base URL")

    args = parser.parse_args()

    examples_dir = Path(__file__).parent

    print("=" * 70)
    print("GenAI Spine - Run All Examples")
    print("=" * 70)

    # Check service
    print(f"\n🔍 Checking GenAI Spine at {args.base_url}...")
    if not check_service(args.base_url):
        print("❌ GenAI Spine is not running!")
        print("\nStart it with:")
        print("  docker compose up -d")
        print("  docker compose exec ollama ollama pull llama3.2:latest")
        sys.exit(1)
    print("✅ Service is running!\n")

    # Determine which examples to run
    if args.only:
        run_numbers = {int(n) for n in args.only.split(",")}
    elif args.quick:
        run_numbers = set(QUICK_EXAMPLES)
    else:
        run_numbers = set(range(1, len(EXAMPLES) + 1))

    if args.skip:
        skip_numbers = {int(n) for n in args.skip.split(",")}
        run_numbers -= skip_numbers

    # Run examples
    results = []
    for i, (script, name, requires_llm) in enumerate(EXAMPLES, 1):
        if i not in run_numbers:
            continue

        script_path = examples_dir / script
        if not script_path.exists():
            print(f"⚠️  {script} not found, skipping...")
            continue

        print(f"\n{'=' * 70}")
        print(f"Example {i:02d}: {name}")
        if requires_llm:
            print("(Requires LLM - may take a moment)")
        print("=" * 70)

        success = run_example(script_path, args.base_url)
        results.append((script, name, success))

        if not success:
            print(f"\n⚠️  Example {script} failed!")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, _, s in results if s)
    failed = len(results) - passed

    for script, name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}  {name}")

    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} examples")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
