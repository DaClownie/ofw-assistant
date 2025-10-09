# app/utils/controlled_taxonomy.py
from typing import List, Dict, Set
import re

class ControlledTaxonomy:
    """Controlled vocabulary system for consistent tagging"""
    
    def __init__(self):
        # Define the master taxonomy with categories and specific tags
        self.taxonomy = {
            # LEGAL CATEGORIES
            "legal_custody": [
                "physical_custody", "legal_custody", "joint_custody", "sole_custody", 
                "custody_modification", "custody_violation", "parenting_plan"
            ],
            "legal_process": [
                "court_order", "hearing", "deposition", "mediation", "contempt", 
                "violation", "compliance", "legal_filing", "attorney_communication"
            ],
            "visitation": [
                "visitation_schedule", "supervised_visitation", "unsupervised_visitation",
                "missed_visitation", "visitation_interference", "makeup_time",
                "holiday_schedule", "vacation_time"
            ],
            
            # CLINICAL/DIAGNOSTIC CATEGORIES  
            "mental_health": [
                "anxiety", "depression", "bipolar", "borderline_personality", 
                "ptsd", "adhd", "autism_spectrum", "conduct_disorder",
                "oppositional_defiant", "attachment_disorder"
            ],
            "medical_concerns": [
                "chronic_illness", "medication_compliance", "medical_neglect",
                "doctor_shopping", "medical_records", "emergency_medical",
                "developmental_delays", "speech_therapy", "occupational_therapy"
            ],
            "evaluations": [
                "psychological_evaluation", "custody_evaluation", "forensic_evaluation",
                "therapeutic_evaluation", "educational_evaluation", "medical_evaluation",
                "home_study", "guardian_ad_litem"
            ],
            
            # BEHAVIORAL CATEGORIES
            "child_behavior": [
                "regression", "acting_out", "school_problems", "peer_issues",
                "sleep_disturbance", "eating_issues", "self_harm", "aggression",
                "withdrawal", "developmental_concerns"
            ],
            "parental_behavior": [
                "alienation", "coaching", "manipulation", "emotional_abuse",
                "neglect", "inconsistent_parenting", "boundary_violations",
                "inappropriate_communication", "gatekeeping"
            ],
            "communication": [
                "hostile_communication", "withholding_information", "false_allegations",
                "documentation", "email_harassment", "social_media", 
                "third_party_communication", "professional_communication"
            ],
            
            # HIGH-RISK FLAGS
            "safety_concerns": [
                "physical_abuse", "sexual_abuse", "substance_abuse",
                "domestic_violence", "suicidal_ideation", "self_harm",
                "dangerous_behavior", "weapon_concerns", "criminal_activity"
            ],
            "fabricated_concerns": [
                "fdia_suspected", "exaggerated_symptoms", "coached_statements",
                "inconsistent_reports", "medical_shopping", "induced_illness",
                "false_emergency", "attention_seeking"
            ],
            
            # PRACTICAL CATEGORIES
            "logistics": [
                "transportation", "childcare", "school_coordination", "activities",
                "financial_support", "insurance", "emergency_contacts",
                "pickup_dropoff", "communication_method"
            ],
            "support_systems": [
                "extended_family", "therapeutic_support", "educational_support",
                "community_resources", "religious_community", "peer_support",
                "professional_network", "crisis_resources"
            ]
        }
        
        # Create reverse lookup for tag to category mapping
        self.tag_to_category = {}
        for category, tags in self.taxonomy.items():
            for tag in tags:
                self.tag_to_category[tag] = category
        
        # Create flat list of all valid tags
        self.valid_tags = set()
        for tags in self.taxonomy.values():
            self.valid_tags.update(tags)
        
        # Define keyword patterns for automatic classification
        self.keyword_patterns = self._build_keyword_patterns()
    
    def _build_keyword_patterns(self) -> Dict[str, List[str]]:
        """Build keyword patterns for each tag"""
        return {
            # Legal patterns
            "physical_custody": ["physical custody", "primary residence", "residential custody"],
            "legal_custody": ["legal custody", "decision making", "legal authority"],
            "court_order": ["court order", "judge ordered", "court mandated", "judicial order"],
            "visitation_schedule": ["visitation", "parenting time", "access schedule"],
            "supervised_visitation": ["supervised", "monitored visit", "supervision required"],
            "contempt": ["contempt", "violation of order", "non-compliance"],
            
            # Clinical patterns
            "anxiety": ["anxiety", "anxious", "worry", "panic", "fear"],
            "depression": ["depression", "depressed", "sad", "hopeless", "suicide"],
            "bipolar": ["bipolar", "manic", "mood swings", "mania"],
            "borderline_personality": ["borderline", "bpd", "unstable relationships"],
            "adhd": ["adhd", "attention deficit", "hyperactive", "focus problems"],
            "autism_spectrum": ["autism", "asperger", "spectrum", "developmental"],
            
            # Behavioral patterns
            "alienation": ["parental alienation", "turning child against", "badmouthing"],
            "coaching": ["coached", "told what to say", "rehearsed", "prompted"],
            "manipulation": ["manipulative", "guilt trip", "emotional manipulation"],
            "regression": ["regression", "baby talk", "bedwetting", "developmental step back"],
            
            # Safety patterns
            "physical_abuse": ["physical abuse", "hitting", "bruises", "injury"],
            "sexual_abuse": ["sexual abuse", "inappropriate touching", "sexual contact"],
            "substance_abuse": ["drugs", "alcohol", "substance", "intoxicated", "impaired"],
            "domestic_violence": ["domestic violence", "dv", "intimate partner violence"],
            
            # Fabricated concerns
            "fdia_suspected": ["fabricated illness", "munchausen", "induced symptoms", "medical abuse"],
            "exaggerated_symptoms": ["exaggerated", "amplified", "overreported", "dramatic"],
            "medical_shopping": ["doctor shopping", "multiple providers", "seeking diagnosis"],
            
            # Communication patterns
            "hostile_communication": ["hostile", "aggressive", "threatening", "inappropriate tone"],
            "false_allegations": ["false allegation", "unfounded", "unsubstantiated"],
            "documentation": ["documentation", "evidence", "records", "log"],
            
            # Logistics
            "transportation": ["transportation", "pickup", "drop off", "driving"],
            "school_coordination": ["school", "education", "teacher", "academic"],
            "activities": ["extracurricular", "sports", "activities", "lessons"]
        }
    
    def classify_text(self, text: str) -> List[str]:
        """Classify text into controlled taxonomy tags"""
        if not text.strip():
            return []
        
        text_lower = text.lower()
        matched_tags = set()
        
        # Pattern matching
        for tag, patterns in self.keyword_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    matched_tags.add(tag)
        
        # Additional context-based rules
        matched_tags.update(self._apply_context_rules(text_lower))
        
        # Ensure all returned tags are in our controlled vocabulary
        valid_matches = [tag for tag in matched_tags if tag in self.valid_tags]
        
        # If no matches, assign default based on content type
        if not valid_matches:
            valid_matches = self._assign_default_tags(text_lower)
        
        return sorted(valid_matches)
    
    def _apply_context_rules(self, text_lower: str) -> Set[str]:
        """Apply contextual rules for better classification"""
        context_tags = set()
        
        # Legal context detection
        legal_indicators = ["court", "judge", "attorney", "lawyer", "order", "hearing"]
        if any(indicator in text_lower for indicator in legal_indicators):
            if "custody" in text_lower:
                context_tags.add("legal_custody")
            if "visit" in text_lower or "parenting time" in text_lower:
                context_tags.add("visitation_schedule")
        
        # Clinical context detection
        clinical_indicators = ["doctor", "therapist", "diagnosis", "treatment", "evaluation"]
        if any(indicator in text_lower for indicator in clinical_indicators):
            if "psych" in text_lower or "mental" in text_lower:
                context_tags.add("psychological_evaluation")
            if "medical" in text_lower:
                context_tags.add("medical_evaluation")
        
        # Safety context detection
        safety_indicators = ["unsafe", "danger", "harm", "abuse", "violence"]
        if any(indicator in text_lower for indicator in safety_indicators):
            context_tags.add("safety_concerns")
        
        # Communication context detection
        comm_indicators = ["email", "text", "message", "communication", "contact"]
        if any(indicator in text_lower for indicator in comm_indicators):
            if any(negative in text_lower for negative in ["hostile", "inappropriate", "threatening"]):
                context_tags.add("hostile_communication")
            else:
                context_tags.add("professional_communication")
        
        return context_tags
    
    def _assign_default_tags(self, text_lower: str) -> List[str]:
        """Assign default tags when no specific matches found"""
        # Basic categorization for unmatched content
        if len(text_lower.split()) < 10:
            return ["documentation"]  # Short texts are likely documentation
        elif any(word in text_lower for word in ["child", "kid", "son", "daughter"]):
            return ["child_behavior"]
        elif any(word in text_lower for word in ["parent", "mom", "dad", "mother", "father"]):
            return ["parental_behavior"]
        else:
            return ["documentation"]  # Default fallback
    
    def get_category_for_tag(self, tag: str) -> str:
        """Get the category for a specific tag"""
        return self.tag_to_category.get(tag, "unknown")
    
    def get_tags_by_category(self, category: str) -> List[str]:
        """Get all tags for a specific category"""
        return self.taxonomy.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        return list(self.taxonomy.keys())
    
    def get_all_tags(self) -> List[str]:
        """Get all available tags"""
        return sorted(list(self.valid_tags))
    
    def validate_tags(self, tags: List[str]) -> List[str]:
        """Validate and filter tags to only include valid ones"""
        return [tag for tag in tags if tag in self.valid_tags]

# Global instance
controlled_taxonomy = ControlledTaxonomy()