#!/usr/bin/env python3
"""Test script to verify Gemini API fallback works directly."""
import os
import sys
import json
import requests
from datetime import datetime

def load_env():
    env_file = ".env"
    if not os.path.exists(env_file):
        return {}
    env_vars = {}
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def test_gemini_api():
    env = load_env()
    api_key = env.get("GEMINI_API_KEY")
    model = env.get("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env")
        return False

    print(f"[*] Testing Gemini API directly with model: {model}")

    prompt = """You are testing the AI Employee task planner. Create a brief execution plan for: 'Setup a new project repository'.

Format:
# Task Execution Plan
## Task Analysis
## Dependencies  
## Step-by-Step Plan (use - [ ] format)
## Complexity: [Low/Medium/High]
## Priority: [Urgent/High/Medium/Low]
"""

    try:
        response = requests.post(
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                plan = data["candidates"][0]["content"]["parts"][0]["text"]
                print("✅ Gemini API responded successfully!")
                print("\n--- Generated Plan ---")
                print(plan[:500])
                print("...\n--- End of Plan ---")
                return True
            else:
                print(f"❌ Unexpected response format: {data}")
                return False
        else:
            print(f"❌ Gemini API error (HTTP {response.status_code}): {response.text}")
            return False

    except Exception as e:
        print(f"❌ Gemini API request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    sys.exit(0 if success else 1)
