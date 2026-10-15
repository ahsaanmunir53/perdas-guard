import os
import sys
sys.path.insert(0, os.path.abspath("backend"))

from app.config import Settings

settings = Settings()

print("LLM backend:", settings.llm_backend)
print("Gemini API key configured:", bool(settings.gemini_api_key))
print("Fast model:", settings.model_fast)
print("Pro model:", settings.model_pro)
print("Google Cloud project configured:", bool(settings.google_cloud_project))
print("Graph backend:", settings.graph_backend)
print("Store backend:", settings.store_backend)
