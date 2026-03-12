#!/usr/bin/env python3
"""
Diagnostic script to test which Gemini models are available and working.
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    sys.exit(1)

print(f"Testing with API key: {api_key[:20]}...")
print("-" * 70)

genai.configure(api_key=api_key)

# Step 1: List all available models
print("\nSTEP 1: Listing all available models...")
try:
    all_models = list(genai.list_models())
    print(f"Found {len(all_models)} total models")
    
    # Filter for generateContent support
    generate_models = [m for m in all_models if 'generateContent' in m.supported_generation_methods]
    print(f"{len(generate_models)} support generateContent")
    
    print("\nAvailable models for generateContent:")
    for model in sorted(generate_models, key=lambda m: m.name):
        model_name = model.name.replace('models/', '')
        print(f"  • {model_name}")
except Exception as e:
    print(f"Error listing models: {e}")
    sys.exit(1)

# Step 2: Test each model with a simple prompt
print("\n" + "-" * 70)
print("STEP 2: Testing each model with a simple prompt...")
print("-" * 70)

test_prompt = "Say 'Hello' in exactly one word."
working_models = []
failed_models = {}

for model in sorted(generate_models, key=lambda m: m.name):
    model_name = model.name.replace('models/', '')
    try:
        print(f"\nTesting {model_name}...", end=" ")
        m = genai.GenerativeModel(model_name)
        response = m.generate_content(test_prompt, timeout=30)
        if response.text:
            print(f"✓ WORKS")
            print(f"  Response: {response.text[:80]}")
            working_models.append(model_name)
        else:
            print(f"⚠ NO RESPONSE")
            failed_models[model_name] = "No response text"
    except Exception as e:
        error_str = str(e)[:120]
        print(f"❌ FAILED")
        print(f"  Error: {error_str}")
        failed_models[model_name] = error_str

# Step 3: Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if working_models:
    print(f"\nWorking models ({len(working_models)}):")
    for model in working_models:
        print(f"  • {model}")
    
    print(f"\nRecommended fallback sequence for gemini.py:")
    print("FALLBACK_MODEL_SEQUENCE = [")
    for model in working_models:
        print(f'    "{model}",')
    print("]")
else:
    print("\nNo models are working!")

if failed_models:
    print(f"\nFailed models ({len(failed_models)}):")
    for model, error in failed_models.items():
        print(f"  • {model}: {error}")
