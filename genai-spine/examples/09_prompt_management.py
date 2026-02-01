#!/usr/bin/env python3
"""Example 09: Prompt Management (CRUD).

Demonstrates:
- Create custom prompts
- List and filter prompts
- Update prompt content (creates new version)
- Prompt versioning and rollback
- Delete prompts

Run:
    docker compose up -d
    python examples/09_prompt_management.py
"""

import httpx
import json
from uuid import uuid4

BASE_URL = "http://localhost:8100"


def main():
    print("=" * 60)
    print("GenAI Spine - Example 09: Prompt Management")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # Generate unique slug for this run
    unique_id = str(uuid4())[:8]

    # 1. Create a New Prompt
    print("\n➕ 1. Create a New Prompt")
    print("-" * 40)

    new_prompt = {
        "name": f"Code Review Prompt {unique_id}",
        "slug": f"code-review-{unique_id}",
        "description": "A prompt for reviewing code quality and suggesting improvements",
        "template": """Review the following code and provide feedback on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Suggestions for improvement

Code to review:
{{code}}

Language: {{language}}
""",
        "category": "development",
        "tags": ["code-review", "development", "quality"],
        "variables": [
            {"name": "code", "description": "The code to review", "required": True},
            {"name": "language", "description": "Programming language", "required": False},
        ],
    }

    response = client.post("/v1/prompts", json=new_prompt)

    if response.status_code in (200, 201):
        data = response.json()
        prompt_id = data.get("id")
        print(f"✅ Created prompt: {data.get('name')}")
        print(f"   ID: {prompt_id}")
        print(f"   Slug: {data.get('slug')}")
        print(f"   Version: {data.get('version', 1)}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return

    # 2. List All Prompts
    print("\n📋 2. List All Prompts")
    print("-" * 40)

    response = client.get("/v1/prompts")

    if response.status_code == 200:
        data = response.json()
        prompts = data.get("prompts", data) if isinstance(data, dict) else data
        print(f"Found {len(prompts)} prompts:")
        for p in prompts[:5]:  # Show first 5
            print(f"  - {p.get('name', 'unnamed')} ({p.get('slug', 'no-slug')})")
    else:
        print(f"❌ Error: {response.status_code}")

    # 3. Get Prompt by ID
    print("\n🔍 3. Get Prompt by ID")
    print("-" * 40)

    response = client.get(f"/v1/prompts/{prompt_id}")

    if response.status_code == 200:
        data = response.json()
        print(f"Name: {data.get('name')}")
        print(f"Category: {data.get('category')}")
        print(f"Tags: {data.get('tags')}")
        print(f"Template preview: {data.get('template', '')[:100]}...")
    else:
        print(f"❌ Error: {response.status_code}")

    # 4. Get Prompt by Slug
    print("\n🏷️ 4. Get Prompt by Slug")
    print("-" * 40)

    response = client.get(f"/v1/prompts/slug/{new_prompt['slug']}")

    if response.status_code == 200:
        data = response.json()
        print(f"Found prompt: {data.get('name')}")
    else:
        print(f"❌ Error: {response.status_code}")

    # 5. Update Prompt (Creates New Version)
    print("\n✏️ 5. Update Prompt (Creates Version 2)")
    print("-" * 40)

    updated_template = """Review the following code with special attention to:
1. Security vulnerabilities
2. Code quality and best practices
3. Performance bottlenecks
4. Test coverage suggestions
5. Documentation needs

Code to review:
{{code}}

Language: {{language}}
Focus areas: {{focus_areas}}
"""

    response = client.put(
        f"/v1/prompts/{prompt_id}",
        json={
            "template": updated_template,
            "variables": [
                {"name": "code", "description": "The code to review", "required": True},
                {"name": "language", "description": "Programming language", "required": False},
                {
                    "name": "focus_areas",
                    "description": "Specific areas to focus on",
                    "required": False,
                },
            ],
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Updated prompt to version {data.get('version', 2)}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

    # 6. List Prompt Versions
    print("\n📚 6. List Prompt Versions")
    print("-" * 40)

    response = client.get(f"/v1/prompts/{prompt_id}/versions")

    if response.status_code == 200:
        data = response.json()
        versions = data.get("versions", data) if isinstance(data, dict) else data
        print(f"Found {len(versions)} versions:")
        for v in versions:
            print(f"  - Version {v.get('version')}: {v.get('created_at', 'unknown date')}")
    else:
        print(f"❌ Error: {response.status_code}")

    # 7. Delete Prompt
    print("\n🗑️ 7. Delete Prompt (Soft Delete)")
    print("-" * 40)

    response = client.delete(f"/v1/prompts/{prompt_id}")

    if response.status_code in (200, 204):
        print(f"✅ Deleted prompt {prompt_id}")
    else:
        print(f"❌ Error: {response.status_code}")

    print("\n" + "=" * 60)
    print("✅ Prompt management examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
