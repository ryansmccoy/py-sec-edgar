#!/usr/bin/env python3
"""Example 03: Text Summarization.

Demonstrates:
- Summarize long text content
- Customize output length (max_sentences)
- Different summary styles

Run:
    docker compose up -d
    python examples/03_summarization.py
"""

import httpx

BASE_URL = "http://localhost:8100"

# Sample long text for summarization
SAMPLE_TEXT = """
The development of artificial intelligence has accelerated dramatically over the past decade,
transforming industries from healthcare to finance. Machine learning algorithms now power
recommendation systems, fraud detection, and autonomous vehicles. Large language models like
GPT-4 and Claude have demonstrated remarkable capabilities in understanding and generating
human-like text, leading to applications in customer service, content creation, and code
generation.

However, these advances come with significant challenges. Concerns about AI safety, bias in
training data, and the potential for misuse have prompted calls for regulation and ethical
guidelines. The environmental impact of training large models, which requires enormous
computational resources, has also drawn attention from sustainability advocates.

Despite these challenges, investment in AI continues to grow. Major tech companies and
startups alike are racing to develop more capable and efficient models. The integration
of AI into everyday tools and workflows is expected to continue, with predictions that
AI will eventually augment most knowledge work tasks.

Looking ahead, researchers are exploring new frontiers including artificial general
intelligence (AGI), multimodal models that combine text, image, and audio understanding,
and AI systems that can reason and plan more effectively. The next decade promises to
bring even more transformative applications of this technology.
"""


def main():
    print("=" * 60)
    print("GenAI Spine - Example 03: Text Summarization")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # 1. Basic Summarization
    print("\n📝 1. Basic Summarization (3 sentences)")
    print("-" * 40)

    response = client.post(
        "/v1/summarize",
        json={
            "content": SAMPLE_TEXT,
            "max_sentences": 3,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Summary:\n{data.get('summary', data)}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

    # 2. Shorter Summary
    print("\n📝 2. Ultra-Short Summary (1 sentence)")
    print("-" * 40)

    response = client.post(
        "/v1/summarize",
        json={
            "content": SAMPLE_TEXT,
            "max_sentences": 1,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Summary:\n{data.get('summary', data)}")
    else:
        print(f"❌ Error: {response.status_code}")

    # 3. Longer Summary
    print("\n📝 3. Detailed Summary (5 sentences)")
    print("-" * 40)

    response = client.post(
        "/v1/summarize",
        json={
            "content": SAMPLE_TEXT,
            "max_sentences": 5,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Summary:\n{data.get('summary', data)}")
    else:
        print(f"❌ Error: {response.status_code}")

    print("\n" + "=" * 60)
    print(f"Original text: {len(SAMPLE_TEXT.split())} words")
    print("✅ Summarization examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
