#!/usr/bin/env python3
"""Example 08: Commit Message Generation.

Demonstrates:
- Generate commit messages from diffs
- Different commit styles (conventional, simple, detailed)
- Include context about the change

Run:
    docker compose up -d
    python examples/08_commit_generation.py
"""

import httpx

BASE_URL = "http://localhost:8100"

# Sample diffs for commit message generation
SAMPLE_DIFFS = [
    {
        "diff": """
diff --git a/src/auth.py b/src/auth.py
index 1234567..abcdefg 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -45,6 +45,12 @@ def authenticate_user(username: str, password: str) -> User:
     if not user:
         raise AuthError("User not found")

+    # Rate limiting: max 5 attempts per minute
+    if get_login_attempts(username) > 5:
+        raise AuthError("Too many login attempts. Please wait 60 seconds.")
+
+    increment_login_attempts(username)
+
     if not verify_password(password, user.password_hash):
         raise AuthError("Invalid password")
""",
        "context": "Adding rate limiting to prevent brute force attacks",
    },
    {
        "diff": """
diff --git a/package.json b/package.json
index 1234567..abcdefg 100644
--- a/package.json
+++ b/package.json
@@ -15,7 +15,7 @@
   "dependencies": {
-    "react": "^17.0.2",
+    "react": "^18.2.0",
-    "react-dom": "^17.0.2",
+    "react-dom": "^18.2.0",
     "axios": "^1.4.0"
   }
""",
        "context": "Upgrading React to version 18 for concurrent features",
    },
    {
        "diff": """
diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,5 +1,25 @@
 # MyProject

-A simple project.
+A powerful data processing library for Python.
+
+## Installation
+
+```bash
+pip install myproject
+```
+
+## Quick Start
+
+```python
+from myproject import process
+result = process(data)
+```
+
+## Features
+
+- Fast data processing
+- Easy to use API
+- Extensive documentation
""",
        "context": "Expanding README with installation and usage instructions",
    },
]


def main():
    print("=" * 60)
    print("GenAI Spine - Example 08: Commit Message Generation")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # 1. Conventional Commit Style
    print("\n📝 1. Conventional Commit Style")
    print("-" * 40)

    for i, sample in enumerate(SAMPLE_DIFFS, 1):
        response = client.post(
            "/v1/generate-commit",
            json={
                "diff": sample["diff"],
                "context": sample["context"],
                "style": "conventional",
            },
        )

        if response.status_code == 200:
            data = response.json()
            message = data.get("message", data.get("commit_message", data))
            print(f"Commit {i}:")
            print(f"  {message}")
            print()
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

    # 2. Simple Style
    print("\n✏️ 2. Simple Commit Style")
    print("-" * 40)

    for i, sample in enumerate(SAMPLE_DIFFS, 1):
        response = client.post(
            "/v1/generate-commit",
            json={
                "diff": sample["diff"],
                "style": "simple",
            },
        )

        if response.status_code == 200:
            data = response.json()
            message = data.get("message", data.get("commit_message", data))
            print(f"Commit {i}: {message}")
        else:
            print(f"❌ Error: {response.status_code}")

    # 3. Detailed Style
    print("\n📋 3. Detailed Commit Style")
    print("-" * 40)

    response = client.post(
        "/v1/generate-commit",
        json={
            "diff": SAMPLE_DIFFS[0]["diff"],
            "context": SAMPLE_DIFFS[0]["context"],
            "style": "detailed",
        },
    )

    if response.status_code == 200:
        data = response.json()
        message = data.get("message", data.get("commit_message", data))
        print(f"Detailed commit message:\n{message}")
    else:
        print(f"❌ Error: {response.status_code}")

    print("\n" + "=" * 60)
    print("✅ Commit generation examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
