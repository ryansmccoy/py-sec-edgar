#!/usr/bin/env python3
"""Example 10: Cost Tracking and Usage Statistics.

Demonstrates:
- Get model pricing information
- Estimate costs before execution
- View usage statistics
- Filter usage by date range

Run:
    docker compose up -d
    python examples/10_cost_tracking.py
"""

import httpx
from datetime import date, timedelta

BASE_URL = "http://localhost:8100"


def main():
    print("=" * 60)
    print("GenAI Spine - Example 10: Cost Tracking & Usage")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. List All Model Pricing
    print("\n💰 1. Model Pricing List")
    print("-" * 40)

    response = client.get("/v1/pricing")

    if response.status_code == 200:
        data = response.json()
        models = data.get("models", data) if isinstance(data, dict) else data
        print(f"{'Model':<30} {'Input/1K':<12} {'Output/1K':<12}")
        print("-" * 54)
        for model in models[:10]:  # Show first 10
            name = model.get("model", model.get("name", "unknown"))
            input_price = model.get("input_price", model.get("input_cost_per_1k", 0))
            output_price = model.get("output_price", model.get("output_cost_per_1k", 0))
            print(f"{name:<30} ${input_price:<11.6f} ${output_price:<11.6f}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

    # 2. Get Specific Model Pricing
    print("\n💵 2. Specific Model Pricing")
    print("-" * 40)

    models_to_check = ["gpt-4o", "gpt-4o-mini", "claude-3-opus", "llama3.2:latest"]

    for model in models_to_check:
        response = client.get(f"/v1/pricing/{model}")

        if response.status_code == 200:
            data = response.json()
            input_price = data.get("input_price", data.get("input_cost_per_1k", 0))
            output_price = data.get("output_price", data.get("output_cost_per_1k", 0))
            print(f"{model}: ${input_price}/1K input, ${output_price}/1K output")
        elif response.status_code == 404:
            print(f"{model}: Free (local model)")
        else:
            print(f"{model}: Error {response.status_code}")

    # 3. Estimate Cost Before Execution
    print("\n📊 3. Cost Estimation")
    print("-" * 40)

    # Estimate for different models
    test_content = "Write a detailed analysis of the current state of artificial intelligence."

    estimates = [
        {"model": "gpt-4o", "input_tokens": 100, "output_tokens": 500},
        {"model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 500},
        {"model": "claude-3-opus-20240229", "input_tokens": 100, "output_tokens": 500},
        {"model": "llama3.2:latest", "input_tokens": 100, "output_tokens": 500},
    ]

    for est in estimates:
        response = client.post(
            "/v1/estimate-cost",
            json={
                "model": est["model"],
                "input_tokens": est["input_tokens"],
                "output_tokens": est["output_tokens"],
            },
        )

        if response.status_code == 200:
            data = response.json()
            total_cost = data.get("total_cost", data.get("estimated_cost", 0))
            print(f"{est['model']:<30} ~${total_cost:.6f}")
        else:
            print(f"{est['model']:<30} Error: {response.status_code}")

    # 4. Get Usage Statistics
    print("\n📈 4. Usage Statistics (All Time)")
    print("-" * 40)

    response = client.get("/v1/usage")

    if response.status_code == 200:
        data = response.json()
        print(f"Total requests: {data.get('total_requests', 0)}")
        print(f"Total tokens: {data.get('total_tokens', 0)}")
        print(f"Total cost: ${data.get('total_cost', 0):.4f}")

        # Show breakdown by provider if available
        by_provider = data.get("by_provider", {})
        if by_provider:
            print("\nBy Provider:")
            for provider, stats in by_provider.items():
                print(
                    f"  {provider}: {stats.get('requests', 0)} requests, ${stats.get('cost', 0):.4f}"
                )
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

    # 5. Get Usage for Last 7 Days
    print("\n📅 5. Usage Statistics (Last 7 Days)")
    print("-" * 40)

    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    response = client.get(
        "/v1/usage",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Period: {start_date} to {end_date}")
        print(f"Requests: {data.get('total_requests', 0)}")
        print(f"Cost: ${data.get('total_cost', 0):.4f}")
    else:
        print(f"❌ Error: {response.status_code}")

    print("\n" + "=" * 60)
    print("✅ Cost tracking examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
