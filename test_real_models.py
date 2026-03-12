#!/usr/bin/env python3
"""Test actual models without timeout parameter."""
import os
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

# Test the modern models that are actually available
models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]

print("Testing available models:")
print("=" * 60)

for model_name in models_to_test:
    try:
        print(f"\nTesting: {model_name}...", end=" ")
        m = genai.GenerativeModel(model_name)
        response = m.generate_content("Say 'Hello' in one word.")
        
        if response.text:
            print(f"✓ WORKS")
            print(f"  Response: {response.text}")
        else:
            print(f"⚠ No response text")
            
    except Exception as e:
        print(f"✗ FAILED: {str(e)[:80]}")

print("\n" + "=" * 60)
print("\nRECOMMENDED FALLBACK SEQUENCE:")
print("FALLBACK_MODEL_SEQUENCE = [")
print('    "gemini-2.5-flash",')
print('    "gemini-2.0-flash",')
print('    "gemini-flash-latest",')
print("]")
