import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from cau_hinh import CauHinh
import numpy as np
from google import genai
from openai import OpenAI

def test():
    print(f"OpenAI Key starting with: {CauHinh.OPENAI_API_KEY[:10]}")
    # Test OpenAI
    o_client = OpenAI(api_key=CauHinh.OPENAI_API_KEY)
    res = o_client.embeddings.create(
        input=["Hello"],
        model="text-embedding-3-small",
        dimensions=768
    )
    o_vec = res.data[0].embedding
    print(f"OpenAI length: {len(o_vec)}")

    # Test Gemini
    g_client = genai.Client(api_key=CauHinh.GEMINI_API_KEYS[0])
    res = g_client.models.embed_content(
        model="models/text-embedding-004",
        contents=["Hello"]
    )
    
    g_vec = None
    if isinstance(res, list):
        g_vec = res[0].values
    else:
        g_vec = res.embeddings[0].values
    print(f"Gemini length: {len(g_vec)}")

if __name__ == "__main__":
    test()
