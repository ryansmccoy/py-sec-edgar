#!/usr/bin/env python3
"""Example 05: Content Classification.

Demonstrates:
- Classify text into categories
- Custom category definitions
- Multi-label classification
- Confidence scores

Run:
    docker compose up -d
    python examples/05_classification.py
"""

import httpx
import json

BASE_URL = "http://localhost:8100"

# Sample texts for classification
SAMPLES = [
    {
        "text": "The S&P 500 rose 2% today following positive earnings reports from major tech companies.",
        "expected": "finance",
    },
    {
        "text": "Scientists at CERN have discovered a new particle that could revolutionize our understanding of physics.",
        "expected": "science",
    },
    {
        "text": "The Lakers defeated the Celtics 112-108 in an overtime thriller last night.",
        "expected": "sports",
    },
    {
        "text": "The new Python 3.12 release includes significant performance improvements and better error messages.",
        "expected": "technology",
    },
    {
        "text": "The Federal Reserve announced a 0.25% interest rate cut, signaling concerns about economic growth.",
        "expected": "finance",
    },
]


def main():
    print("=" * 60)
    print("GenAI Spine - Example 05: Content Classification")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # 1. Basic Classification
    print("\n📂 1. Basic Category Classification")
    print("-" * 40)

    categories = ["finance", "technology", "science", "sports", "politics", "entertainment"]

    for i, sample in enumerate(SAMPLES, 1):
        response = client.post(
            "/v1/classify",
            json={
                "content": sample["text"],
                "categories": categories,
            },
        )

        if response.status_code == 200:
            data = response.json()
            predicted = data.get("category", data.get("classification", "unknown"))
            match = "✅" if sample["expected"] in str(predicted).lower() else "❓"
            print(f"{match} Sample {i}: {predicted}")
            print(f"   Text: {sample['text'][:60]}...")
        else:
            print(f"❌ Error: {response.status_code}")

    # 2. Sentiment Classification
    print("\n😊 2. Sentiment Classification")
    print("-" * 40)

    sentiment_texts = [
        "I absolutely love this product! Best purchase I've ever made.",
        "This is the worst service I've experienced. Total waste of money.",
        "The product works as expected. Nothing special but does the job.",
    ]

    for text in sentiment_texts:
        response = client.post(
            "/v1/classify",
            json={
                "content": text,
                "categories": ["positive", "negative", "neutral"],
            },
        )

        if response.status_code == 200:
            data = response.json()
            sentiment = data.get("category", data.get("classification", "unknown"))
            print(f"Sentiment: {sentiment}")
            print(f"   Text: {text[:50]}...")
        else:
            print(f"❌ Error: {response.status_code}")

    # 3. Custom Categories
    print("\n🏷️ 3. Custom Category Classification (Email Triage)")
    print("-" * 40)

    emails = [
        "URGENT: Server down in production. Need immediate assistance!",
        "Meeting reminder: Q4 planning session tomorrow at 2pm",
        "Your order #12345 has been shipped and will arrive Friday",
    ]

    custom_categories = ["urgent", "meeting", "notification", "spam", "personal"]

    for email in emails:
        response = client.post(
            "/v1/classify",
            json={
                "content": email,
                "categories": custom_categories,
            },
        )

        if response.status_code == 200:
            data = response.json()
            category = data.get("category", data.get("classification", "unknown"))
            print(f"Category: {category}")
            print(f"   Email: {email[:50]}...")
        else:
            print(f"❌ Error: {response.status_code}")

    print("\n" + "=" * 60)
    print("✅ Classification examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
