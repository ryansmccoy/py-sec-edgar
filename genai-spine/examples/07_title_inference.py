#!/usr/bin/env python3
"""Example 07: Title Inference.

Demonstrates:
- Generate titles from content
- Control title length with max_words
- Generate headlines for articles/documents

Run:
    docker compose up -d
    python examples/07_title_inference.py
"""

import httpx

BASE_URL = "http://localhost:8100"

# Sample content for title generation
SAMPLES = [
    """
    Today we're releasing version 2.0 of our open-source database library. This major
    update includes a completely rewritten query engine that's 5x faster, native support
    for JSON documents, and improved connection pooling. We've also added real-time
    replication and automatic failover for production deployments.
    """,
    """
    After three months of testing in beta, we're excited to announce that our mobile
    app is now available on both iOS and Android. Users can track their fitness goals,
    connect with friends, and earn rewards for hitting milestones. Early feedback has
    been overwhelmingly positive, with a 4.8 star rating in the App Store.
    """,
    """
    The quarterly earnings report shows revenue up 23% year-over-year, driven primarily
    by growth in our cloud services division. Operating margin improved to 18%, and
    we're raising our full-year guidance. The board has approved a new $500M share
    buyback program.
    """,
    """
    Our team has discovered a critical vulnerability in the widely-used authentication
    library. We're working with the maintainers to issue a patch and recommend all users
    update immediately. The vulnerability allows remote code execution through specially
    crafted JWT tokens.
    """,
]


def main():
    print("=" * 60)
    print("GenAI Spine - Example 07: Title Inference")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # 1. Generate Titles for Each Sample
    print("\n📰 1. Generate Titles (Default Length)")
    print("-" * 40)

    for i, content in enumerate(SAMPLES, 1):
        response = client.post(
            "/v1/infer-title",
            json={
                "content": content.strip(),
            },
        )

        if response.status_code == 200:
            data = response.json()
            title = data.get("title", data)
            print(f"Sample {i}: {title}")
            print(f"   Content: {content.strip()[:60]}...")
            print()
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

    # 2. Short Titles (3 words max)
    print("\n📌 2. Short Titles (max 3 words)")
    print("-" * 40)

    for i, content in enumerate(SAMPLES, 1):
        response = client.post(
            "/v1/infer-title",
            json={
                "content": content.strip(),
                "max_words": 3,
            },
        )

        if response.status_code == 200:
            data = response.json()
            title = data.get("title", data)
            print(f"Sample {i}: {title}")
        else:
            print(f"❌ Error: {response.status_code}")

    # 3. Longer, Descriptive Titles
    print("\n📜 3. Descriptive Titles (max 10 words)")
    print("-" * 40)

    for i, content in enumerate(SAMPLES, 1):
        response = client.post(
            "/v1/infer-title",
            json={
                "content": content.strip(),
                "max_words": 10,
            },
        )

        if response.status_code == 200:
            data = response.json()
            title = data.get("title", data)
            print(f"Sample {i}: {title}")
        else:
            print(f"❌ Error: {response.status_code}")

    print("\n" + "=" * 60)
    print("✅ Title inference examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
