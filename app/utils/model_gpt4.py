# app/utils/model_gpt4.py

from openai import OpenAI
from dotenv import load_dotenv
import os

# Ensure .env is loaded (if not already handled globally)
load_dotenv()

# Instantiate client using env-based API key
def get_client():
    """Get OpenAI client, initializing only when needed"""
    if not hasattr(get_client, '_client'):
        get_client._client = OpenAI()
    return get_client._client

def tag_with_gpt4(text: str) -> list[str]:
    client = get_client()  # Get client here instead
    from .project_settings import load_project_settings
    settings = load_project_settings()
    custom_instructions = settings.get("instructions", "")
    
    system_content = (
        "You are a tagging assistant. Your role is to extract short, relevant issue tags "
        "from legal or clinical documents, especially around parenting, diagnosis, emotional conflict, or legal disputes."
    )
    
    if custom_instructions:
        system_content += f"\n\nAdditional instructions: {custom_instructions}"
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system_content,
            },
            {
                "role": "user",
                "content": f"Please extract concise tags from the following text:\n\n{text}"
            }
        ],
        temperature=0.3,
        max_tokens=150,
    )

    result = response.choices[0].message.content
    tags = [t.strip().lower() for t in result.split(",") if t.strip()]
    return tags

def generate_memo_with_gpt4(text):
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",  # or another model you have access to
        messages=[
            {"role": "system", "content": (
                "You are a legal analyst assistant. Given the following extracted notes and tag summaries "
                "from case-related files, write a concise but insightful memo. "
                "Focus on parenting concerns, diagnoses, manipulative behaviors, and family dynamics. "
                "Keep the tone professional, factual, and well-structured."
            )},
            {"role": "user", "content": text}
        ],
        temperature=0.5,
        max_tokens=800
    )
    return response.choices[0].message.content.strip()