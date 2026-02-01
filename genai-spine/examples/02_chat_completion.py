#!/usr/bin/env python3
"""Example 02: Chat Completion (OpenAI-Compatible).

Demonstrates:
- OpenAI-compatible chat completion API
- Message formatting (system, user, assistant)
- Streaming vs non-streaming responses
- Temperature and max_tokens parameters

Run:
    docker compose up -d
    docker compose exec ollama ollama pull llama3.2:latest
    python examples/02_chat_completion.py
"""

import httpx
import json

BASE_URL = "http://localhost:8100"


def main():
    print("=" * 60)
    print("GenAI Spine - Example 02: Chat Completion")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # 1. Simple Chat Completion
    print("\n💬 1. Simple Chat Completion")
    print("-" * 40)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "llama3.2:latest",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python in one sentence?"},
            ],
            "max_tokens": 100,
            "temperature": 0.7,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Model: {data.get('model')}")
        print(f"Response: {data['choices'][0]['message']['content']}")
        usage = data.get("usage", {})
        print(
            f"Tokens: {usage.get('prompt_tokens', 0)} in, {usage.get('completion_tokens', 0)} out"
        )
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

    # 2. Multi-turn Conversation
    print("\n💬 2. Multi-turn Conversation")
    print("-" * 40)

    conversation = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "What's a list comprehension in Python?"},
        {
            "role": "assistant",
            "content": "A list comprehension is a concise way to create lists in Python using a single line of code.",
        },
        {"role": "user", "content": "Give me a simple example."},
    ]

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "llama3.2:latest",
            "messages": conversation,
            "max_tokens": 150,
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['choices'][0]['message']['content']}")
    else:
        print(f"❌ Error: {response.status_code}")

    # 3. Creative vs Precise (Temperature)
    print("\n💬 3. Temperature Comparison")
    print("-" * 40)

    for temp in [0.1, 0.9]:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "llama3.2:latest",
                "messages": [{"role": "user", "content": "Write a one-line poem about code."}],
                "max_tokens": 50,
                "temperature": temp,
            },
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Temperature {temp}: {data['choices'][0]['message']['content'].strip()}")

    print("\n" + "=" * 60)
    print("✅ Chat completion examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
