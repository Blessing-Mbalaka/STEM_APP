#!/usr/bin/env python3
"""Test the chatbot API directly."""
import os
import sys
import django
from dotenv import load_dotenv

load_dotenv()

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stem_app.settings')
django.setup()

from main.views.gemini import ask_gemini

print("Testing chatbot with Gemini API...")
print("=" * 70)

test_question = "What is the capital of France?"

try:
    print(f"\nQuestion: {test_question}")
    print("Waiting for response...")
    
    response = ask_gemini(test_question)
    
    print(f"\nResponse:")
    print(f"  {response}")
    
    if "error" in response.lower() or "sorry" in response.lower():
        print("\n✗ ERROR RESPONSE")
        sys.exit(1)
    else:
        print("\n✓ SUCCESS!")
        sys.exit(0)
        
except Exception as e:
    print(f"\n✗ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
