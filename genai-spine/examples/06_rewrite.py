#!/usr/bin/env python3
"""Example 06: Content Rewriting (Message Enrichment).

Demonstrates:
- Rewrite modes: clean, format, organize, summarize
- Message enrichment for better readability
- Cleaning up rough notes into professional text

Run:
    docker compose up -d
    python examples/06_rewrite.py
"""

import httpx
import json

BASE_URL = "http://localhost:8100"

ROUGH_NOTES = """
meeting w/ john tmrw 2pm re: Q4 budget
- need to discuss marketing spend (prob 500k?)
- also talk abt new hires - 3 devs + 1 PM
- john mentioned potential office expansion... austin maybe??
- follow up on vendor contracts expiring dec 31
- IMPORTANT: get approval for cloud migration before EOY
btw sarah mentioned sales r up 15% this qtr - nice!
"""

MESSY_EMAIL = """
hey so i was thinking about what you said about the project and i think we should
probably maybe look into using kubernetes for the deployment because like docker
swarm is fine but k8s has better scaling and also the team already knows it from
the last project and also we could use helm charts for the configs and stuff and
also i heard that the new version has better security features but idk we should
probably test it first before committing to anything major you know what i mean
"""


def main():
    print("=" * 60)
    print("GenAI Spine - Example 06: Content Rewriting")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # 1. Clean Mode - Fix grammar, spelling, punctuation
    print("\n🧹 1. Clean Mode (Fix grammar/spelling)")
    print("-" * 40)
    print(f"Original:\n{ROUGH_NOTES[:200]}...")

    response = client.post(
        "/v1/rewrite",
        json={
            "content": ROUGH_NOTES,
            "mode": "clean",
        },
    )

    if response.status_code == 200:
        data = response.json()
        rewritten = data.get("rewritten", data.get("content", data))
        print(f"\nCleaned:\n{rewritten}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

    # 2. Format Mode - Structure into proper format
    print("\n📋 2. Format Mode (Structure content)")
    print("-" * 40)

    response = client.post(
        "/v1/rewrite",
        json={
            "content": ROUGH_NOTES,
            "mode": "format",
        },
    )

    if response.status_code == 200:
        data = response.json()
        rewritten = data.get("rewritten", data.get("content", data))
        print(f"Formatted:\n{rewritten}")
    else:
        print(f"❌ Error: {response.status_code}")

    # 3. Organize Mode - Group related items
    print("\n🗂️ 3. Organize Mode (Group related items)")
    print("-" * 40)

    response = client.post(
        "/v1/rewrite",
        json={
            "content": ROUGH_NOTES,
            "mode": "organize",
        },
    )

    if response.status_code == 200:
        data = response.json()
        rewritten = data.get("rewritten", data.get("content", data))
        print(f"Organized:\n{rewritten}")
    else:
        print(f"❌ Error: {response.status_code}")

    # 4. Summarize Mode - Condense to key points
    print("\n📝 4. Summarize Mode (Condense content)")
    print("-" * 40)

    response = client.post(
        "/v1/rewrite",
        json={
            "content": ROUGH_NOTES,
            "mode": "summarize",
        },
    )

    if response.status_code == 200:
        data = response.json()
        rewritten = data.get("rewritten", data.get("content", data))
        print(f"Summarized:\n{rewritten}")
    else:
        print(f"❌ Error: {response.status_code}")

    # 5. Clean up messy email
    print("\n✉️ 5. Clean Mode on Messy Email")
    print("-" * 40)
    print(f"Original:\n{MESSY_EMAIL[:150]}...")

    response = client.post(
        "/v1/rewrite",
        json={
            "content": MESSY_EMAIL,
            "mode": "clean",
        },
    )

    if response.status_code == 200:
        data = response.json()
        rewritten = data.get("rewritten", data.get("content", data))
        print(f"\nCleaned:\n{rewritten}")
    else:
        print(f"❌ Error: {response.status_code}")

    print("\n" + "=" * 60)
    print("✅ Rewrite examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
