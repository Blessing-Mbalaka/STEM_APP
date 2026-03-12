#!/usr/bin/env python3
"""
Detailed test to find working models and fix fallback sequence.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found")
    sys.exit(1)

print(f"API Key: {api_key[:20]}...")
print("=" * 80)

# Step 1: Configure and list models
print("\n[STEP 1] Listing available models...")
try:
    genai.configure(api_key=api_key)
    all_models = list(genai.list_models())
    print(f"✓ Total models: {len(all_models)}\n")
    
    # Show all models
    print("All available models:")
    for m in all_models:
        print(f"  - {m.name}")
        
except Exception as e:
    print(f"✗ Error listing models: {e}")
    sys.exit(1)

# Step 2: Test each model with generateContent
print("\n" + "=" * 80)
print("[STEP 2] Testing models with generateContent...")
print("=" * 80)

models_to_test = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.5-flash-latest",
    "gemini-2.0-flash-exp",
    "gemini-2.5-flash",
    "gemini-pro",
    "text-embedding-004",
]

working = []
failed = {}

for model_name in models_to_test:
    try:
        print(f"\nTesting: {model_name}...", end=" ")
        m = genai.GenerativeModel(model_name)
        response = m.generate_content("Say hello in one word.", timeout=30)
        
        if response.text:
            print(f"✓ WORKS")
            print(f"  Response: {response.text}")
            working.append(model_name)
        else:
            print(f"⚠ No response text")
            failed[model_name] = "No response text"
            
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"✗ FAILED")
        print(f"  Error: {error_msg}")
        failed[model_name] = error_msg

# Step 3: Summary with recommended sequence
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if working:
    print(f"\n✓ WORKING MODELS ({len(working)}):")
    for m in working:
        print(f"  • {m}")
    
    print(f"\nRECOMMENDED FALLBACK SEQUENCE for gemini.py:")
    print("\nFALLBACK_MODEL_SEQUENCE = [")
    for m in working:
        print(f'    "{m}",')
    print("]")
else:
    print("\n✗ NO WORKING MODELS FOUND")
    print("  This likely means the API key is invalid or disabled")

if failed:
    print(f"\n✗ FAILED MODELS ({len(failed)}):")
    for m, error in list(failed.items())[:5]:
        print(f"  • {m}: {error}")
