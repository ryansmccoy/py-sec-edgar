#!/usr/bin/env python3
"""Example 01: Health Check and Service Discovery.

Demonstrates:
- Health endpoint verification
- Readiness check
- Listing available models
- Service status inspection

Run:
    docker compose up -d
    python examples/01_health_check.py
"""

import httpx
import sys

BASE_URL = "http://localhost:8100"


def main():
    print("=" * 60)
    print("GenAI Spine - Example 01: Health Check & Service Discovery")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. Health Check
    print("\n📊 1. Health Check")
    print("-" * 40)
    try:
        response = client.get("/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except httpx.ConnectError:
        print("❌ Cannot connect to GenAI Spine. Is Docker running?")
        print("   Run: docker compose up -d")
        sys.exit(1)

    # 2. Readiness Check
    print("\n📊 2. Readiness Check")
    print("-" * 40)
    response = client.get("/ready")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # 3. List Available Models
    print("\n📊 3. Available Models")
    print("-" * 40)
    response = client.get("/v1/models")
    data = response.json()
    print(f"Found {len(data.get('data', []))} models:")
    for model in data.get("data", [])[:5]:  # Show first 5
        print(f"  - {model.get('id', 'unknown')}")

    # 4. Get OpenAPI Docs URL
    print("\n📊 4. API Documentation")
    print("-" * 40)
    print(f"Swagger UI: {BASE_URL}/docs")
    print(f"ReDoc: {BASE_URL}/redoc")
    print(f"OpenAPI JSON: {BASE_URL}/openapi.json")

    print("\n" + "=" * 60)
    print("✅ Health check complete! GenAI Spine is running.")
    print("=" * 60)


if __name__ == "__main__":
    main()
