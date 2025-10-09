# app/utils/controlled_smart_tagger.py
import hashlib
import json
from pathlib import Path
from typing import List, Dict
from .controlled_taxonomy import controlled_taxonomy
from .model_gpt4 import tag_with_gpt4
from .model_llama import tag_with_llama

# Cache for avoiding redundant API calls
CACHE_PATH = Path("data/tagging_cache.json")
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

class ControlledSmartTagger:
    """Smart tagger that uses controlled vocabulary"""
    
    def __init__(self):
        self.cache = self._load_cache()
        self.taxonomy = controlled_taxonomy
        self.high_priority_categories = [
            "safety_concerns", "fabricated_concerns", "legal_process", 
            "mental_health", "evaluations"
        ]
    
    def _load_cache(self) -> Dict:
        """Load tagging cache"""
        if CACHE_PATH.exists():
            with open(CACHE_PATH, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        with open(CACHE_PATH, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _get_text_hash(self, text: str) -> str:
        """Generate hash for caching"""
        return hashlib.md5(text.encode()).hexdigest()[:16]
    
    def should_use_gpt4(self, text: str) -> bool:
        """Determine if GPT-4 should be used for this text"""
        text_lower = text.lower()
        
        # Use GPT-4 for high-priority content
        high_priority_keywords = [
            "court order", "custody", "evaluation", "diagnosis", "abuse", 
            "fdia", "munchausen", "fabricated", "borderline", "bipolar", 
            "manipulation", "coaching", "safety", "danger", "harm"
        ]
        
        if any(keyword in text_lower for keyword in high_priority_keywords):
            return True
        
        # Use GPT-4 for longer, complex texts
        if len(text.split()) > 200:
            return True
        
        return False
    
    def tag_text(self, text: str, force_local: bool = False) -> List[str]:
        """Tag text using controlled vocabulary"""
        if not text.strip():
            return []
        
        # Check cache first
        text_hash = self._get_text_hash(text)
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        # Start with pattern-based classification (fast, local)
        local_tags = self.taxonomy.classify_text(text)
        
        # Decide whether to enhance with AI models
        if force_local or not self.should_use_gpt4(text):
            # Use local classification only
            final_tags = local_tags
        else:
            # Enhance with AI model for complex cases
            final_tags = self._enhance_with_ai(text, local_tags)
        
        # Ensure all tags are valid
        final_tags = self.taxonomy.validate_tags(final_tags)
        
        # Cache the result
        self.cache[text_hash] = final_tags
        self._save_cache()
        
        return final_tags
    
    def _enhance_with_ai(self, text: str, local_tags: List[str]) -> List[str]:
        """Enhance local tags with AI model classification"""
        try:
            # Create a focused prompt for the AI
            valid_tags_str = ", ".join(self.taxonomy.get_all_tags())
            
            prompt = f"""
            Classify this text using ONLY the following predefined tags: {valid_tags_str}
            
            Text to classify: {text}
            
            Initial classification: {', '.join(local_tags)}
            
            Return only the most relevant tags from the predefined list, separated by commas.
            Do not create new tags. Only use the exact tags provided above.
            """
            
            if self.should_use_gpt4(text):
                ai_response = tag_with_gpt4(prompt)
            else:
                ai_response = tag_with_llama(prompt)
            
            # Parse AI response and validate tags
            if isinstance(ai_response, list):
                ai_tags = ai_response
            else:
                # If response is a string, split by commas
                ai_tags = [tag.strip().lower() for tag in ai_response.split(',')]
            
            # Combine local and AI tags, remove duplicates
            combined_tags = list(set(local_tags + ai_tags))
            
            # Validate all tags are in our controlled vocabulary
            valid_combined = self.taxonomy.validate_tags(combined_tags)
            
            return valid_combined if valid_combined else local_tags
            
        except Exception as e:
            print(f"⚠️ AI enhancement failed: {e}")
            # Fall back to local tags
            return local_tags
    
    def get_tag_categories(self, tags: List[str]) -> Dict[str, List[str]]:
        """Group tags by their categories"""
        categorized = {}
        for tag in tags:
            category = self.taxonomy.get_category_for_tag(tag)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(tag)
        return categorized
    
    def get_priority_tags(self, tags: List[str]) -> List[str]:
        """Get high-priority tags from the list"""
        priority_tags = []
        for tag in tags:
            category = self.taxonomy.get_category_for_tag(tag)
            if category in self.high_priority_categories:
                priority_tags.append(tag)
        return priority_tags
    
    def analyze_text_comprehensive(self, text: str) -> Dict:
        """Comprehensive analysis returning tags, categories, and priorities"""
        tags = self.tag_text(text)
        
        return {
            'tags': tags,
            'categories': self.get_tag_categories(tags),
            'priority_tags': self.get_priority_tags(tags),
            'tag_count': len(tags),
            'has_safety_concerns': any(
                self.taxonomy.get_category_for_tag(tag) == 'safety_concerns' 
                for tag in tags
            ),
            'has_fabricated_concerns': any(
                self.taxonomy.get_category_for_tag(tag) == 'fabricated_concerns' 
                for tag in tags
            )
        }

# Global instance
controlled_smart_tagger = ControlledSmartTagger()