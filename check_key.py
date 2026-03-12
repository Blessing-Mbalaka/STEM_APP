#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Fresh reload
load_dotenv(override=True)

key = os.getenv('GEMINI_API_KEY', 'NOT FOUND')
print(f"GEMINI_API_KEY from environment: {key[:30]}...")
print(f"Full key: {key}")
