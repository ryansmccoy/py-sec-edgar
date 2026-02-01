#!/usr/bin/env python3
"""Example 04: Entity Extraction.

Demonstrates:
- Extract named entities from text
- Specify entity types (PERSON, ORG, LOCATION, etc.)
- Extract key points and concepts

Run:
    docker compose up -d
    python examples/04_entity_extraction.py
"""

import httpx
import json

BASE_URL = "http://localhost:8100"

SAMPLE_NEWS = """
Apple CEO Tim Cook announced today that the company will invest $1 billion in a new
research facility in Austin, Texas. The facility, expected to open in 2027, will focus
on artificial intelligence and machine learning research. Cook made the announcement
during a press conference at Apple Park in Cupertino, California.

"This investment represents our commitment to American innovation," Cook said. The
project has received support from Texas Governor Greg Abbott and Austin Mayor Kirk Watson.
Apple's chief technology officer, Craig Federighi, will oversee the new facility's
development alongside VP of Machine Learning, John Giannandrea.

The move follows similar investments by Microsoft in Seattle and Google in New York City.
Industry analysts from Goldman Sachs and Morgan Stanley have praised the decision,
predicting it will create over 5,000 new jobs in the Austin area.
"""


def main():
    print("=" * 60)
    print("GenAI Spine - Example 04: Entity Extraction")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # 1. Extract People
    print("\n👤 1. Extract People (PERSON)")
    print("-" * 40)

    response = client.post(
        "/v1/extract",
        json={
            "content": SAMPLE_NEWS,
            "entity_types": ["PERSON"],
        },
    )

    if response.status_code == 200:
        data = response.json()
        entities = data.get("entities", data)
        print(f"Found entities: {json.dumps(entities, indent=2)}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

    # 2. Extract Organizations
    print("\n🏢 2. Extract Organizations (ORG)")
    print("-" * 40)

    response = client.post(
        "/v1/extract",
        json={
            "content": SAMPLE_NEWS,
            "entity_types": ["ORG"],
        },
    )

    if response.status_code == 200:
        data = response.json()
        entities = data.get("entities", data)
        print(f"Found entities: {json.dumps(entities, indent=2)}")
    else:
        print(f"❌ Error: {response.status_code}")

    # 3. Extract Locations
    print("\n📍 3. Extract Locations (LOCATION)")
    print("-" * 40)

    response = client.post(
        "/v1/extract",
        json={
            "content": SAMPLE_NEWS,
            "entity_types": ["LOCATION"],
        },
    )

    if response.status_code == 200:
        data = response.json()
        entities = data.get("entities", data)
        print(f"Found entities: {json.dumps(entities, indent=2)}")
    else:
        print(f"❌ Error: {response.status_code}")

    # 4. Extract All Entity Types
    print("\n🔍 4. Extract All Entity Types")
    print("-" * 40)

    response = client.post(
        "/v1/extract",
        json={
            "content": SAMPLE_NEWS,
            "entity_types": ["PERSON", "ORG", "LOCATION", "DATE", "MONEY"],
        },
    )

    if response.status_code == 200:
        data = response.json()
        entities = data.get("entities", data)
        print(f"Found entities: {json.dumps(entities, indent=2)}")
    else:
        print(f"❌ Error: {response.status_code}")

    print("\n" + "=" * 60)
    print("✅ Entity extraction examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
