def hybrid_tag(text):
    if "court" in text.lower():
        return ["legal", "court"]
    if "diagnosis" in text.lower():
        return ["clinical", "diagnosis"]
    return ["general"]

def detect_flags(text: str) -> list:
    flags = []

    flag_triggers = {
        "fdia": ["fabricated illness", "medical abuse", "induced symptoms", "hospital hopping"],
        "diagnostic_exaggeration": ["borderline", "bipolar", "spectrum", "doctor said", "multiple evaluations"],
        "manipulative_language": ["parent coaching", "coached", "told me to say", "if I tell the truth"]
    }

    lower_text = text.lower()
    for label, keywords in flag_triggers.items():
        if any(k in lower_text for k in keywords):
            flags.append(label)

    return flags

from app.utils.model_llama import tag_with_llama
from app.utils.model_gpt4 import tag_with_gpt4

def should_use_gpt4(text: str) -> bool:
    return len(text.split()) > 300 or any(
        phrase in text.lower() for phrase in ["diagnosis", "fdia", "evaluation"]
    )

def generate_summary(text: str) -> str:
    if should_use_gpt4(text):
        prompt = (
            "You are a case documentation assistant.\n"
            "Summarize the following text for a parenting, co-parenting, or custody context.\n"
            "Highlight unusual claims, diagnostic language, or behavioral inconsistencies.\n\n"
            f"Text:\n{text}\n\nSummary:"
        )
        return tag_with_gpt4(prompt)
    else:
        return tag_with_llama(f"Summarize:\n{text}")
