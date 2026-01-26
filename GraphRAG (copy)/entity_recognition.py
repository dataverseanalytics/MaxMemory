"""
Entity Recognition Module
Automated entity recognition and extraction using NLP
Supports: spaCy (fast NER) and OpenAI (high quality extraction)
"""

import os
import json
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ========================
# SPACY-BASED NER (Free & Fast)
# ========================

try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("[INFO] Downloading spaCy model 'en_core_web_sm'...")
        os.system("python -m spacy download en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None

# ========================
# OPENAI-BASED NER (High Quality)
# ========================

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
    else:
        OPENAI_AVAILABLE = False
except ImportError:
    OPENAI_AVAILABLE = False
    llm = None


class EntityRecognizer:
    """Automated entity recognition using NLP/OpenAI"""
    
    def __init__(self, use_method="spacy"):
        """
        Initialize entity recognizer
        
        Args:
            use_method: "spacy" (fast, free) or "openai" (high quality, costs money)
        """
        self.use_method = use_method
        self.entities_cache = {}
        
        if use_method == "spacy" and not SPACY_AVAILABLE:
            print("[WARNING] spaCy not available, falling back to OpenAI")
            self.use_method = "openai"
        
        if use_method == "openai" and not OPENAI_AVAILABLE:
            print("[WARNING] OpenAI not available, falling back to spaCy")
            self.use_method = "spacy"
        
        print(f"[INIT] Entity recognition using: {self.use_method.upper()}")
    
    # ========================================
    # METHOD 1: SPACY-BASED (Fast, Free)
    # ========================================
    
    def extract_entities_spacy(self, text: str) -> Dict:
        """
        Extract entities using spaCy NLP
        
        Args:
            text: Input text to extract entities from
        
        Returns:
            Dictionary with entity types and values
        """
        if not SPACY_AVAILABLE:
            return {}
        
        doc = nlp(text)
        
        entities = {
            "PERSON": [],
            "ORG": [],
            "GPE": [],  # Geopolitical entity (location)
            "DATE": [],
            "PRODUCT": [],
            "OTHER": []
        }
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["PERSON"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["ORG"].append(ent.text)
            elif ent.label_ in ["GPE", "LOC"]:
                entities["GPE"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["DATE"].append(ent.text)
            elif ent.label_ == "PRODUCT":
                entities["PRODUCT"].append(ent.text)
            else:
                entities["OTHER"].append({ent.text: ent.label_})
        
        # Remove duplicates
        for key in entities:
            if isinstance(entities[key], list) and entities[key] and isinstance(entities[key][0], dict):
                continue
            entities[key] = list(set(entities[key]))
        
        return {k: v for k, v in entities.items() if v}  # Return only non-empty
    
    # ========================================
    # METHOD 2: OPENAI-BASED (High Quality)
    # ========================================
    
    def extract_entities_openai(self, text: str) -> Dict:
        """
        Extract entities using OpenAI Chat API
        Provides higher quality extraction with context understanding
        
        Args:
            text: Input text to extract entities from
        
        Returns:
            Dictionary with entity types and values
        """
        if not OPENAI_AVAILABLE:
            return {}
        
        prompt = f"""Extract all entities from this text and categorize them.

Text: "{text}"

Return ONLY valid JSON (no markdown, no extra text):
{{
  "PERSON": ["person1", "person2"],
  "ORGANIZATION": ["org1", "org2"],
  "LOCATION": ["location1", "location2"],
  "DATE": ["date1"],
  "PRODUCT": ["product1"],
  "relationships": [
    {{"entity1": "person1", "entity2": "org1", "type": "WORKS_AT"}},
    {{"entity1": "person1", "entity2": "person2", "type": "FRIEND_OF"}}
  ]
}}

Extract all entities. Return empty arrays for categories with no entities."""
        
        try:
            response = llm.invoke(prompt)
            result = json.loads(response.content)
            # Remove empty arrays
            return {k: v for k, v in result.items() if v}
        except Exception as e:
            print(f"[ERROR] OpenAI extraction failed: {e}")
            return {}
    
    # ========================================
    # PUBLIC API
    # ========================================
    
    def extract_entities(self, text: str) -> Dict:
        """
        Extract entities using configured method
        
        Args:
            text: Input text
        
        Returns:
            Dictionary with extracted entities
        """
        if self.use_method == "spacy":
            return self.extract_entities_spacy(text)
        else:
            return self.extract_entities_openai(text)
    
    def extract_and_store(self, text: str, source: str = "document") -> Dict:
        """
        Extract entities and store in cache
        
        Args:
            text: Input text
            source: Source of the text
        
        Returns:
            Extracted entities
        """
        entities = self.extract_entities(text)
        
        # Store in cache with source info
        cache_key = text[:50]
        self.entities_cache[cache_key] = {
            "text": text,
            "source": source,
            "entities": entities
        }
        
        return entities
    
    def print_extracted_entities(self, text: str):
        """Pretty print extracted entities"""
        entities = self.extract_entities(text)
        
        print(f"\n{'='*60}")
        print(f"[EXTRACTED ENTITIES FROM TEXT]")
        print(f"{'='*60}")
        print(f"\nText: {text[:100]}...")
        print(f"\n{'-'*60}")
        
        if not entities:
            print("[INFO] No entities found")
            return
        
        for entity_type, values in entities.items():
            if entity_type == "relationships":
                print(f"\n[RELATIONSHIPS]")
                for rel in values:
                    print(f"  • {rel.get('entity1', '?')} --[{rel.get('type', '?')}]--> {rel.get('entity2', '?')}")
            else:
                print(f"\n[{entity_type}]")
                for value in values:
                    if isinstance(value, dict):
                        print(f"  • {value}")
                    else:
                        print(f"  • {value}")
        
        print(f"\n{'='*60}")


# ========================
# INTEGRATION WITH MEMORY
# ========================

def extract_entities_from_chunk(chunk: str, method: str = "spacy") -> Dict:
    """
    Helper function to extract entities from a chunk
    
    Args:
        chunk: Text chunk
        method: "spacy" or "openai"
    
    Returns:
        Extracted entities
    """
    recognizer = EntityRecognizer(use_method=method)
    return recognizer.extract_entities(chunk)


# ========================
# COMPARISON: SPACY vs OPENAI
# ========================

def compare_extraction_methods(text: str):
    """Compare spaCy vs OpenAI extraction on the same text"""
    
    print(f"\n{'='*70}")
    print(f"[COMPARISON: spaCy vs OpenAI Entity Extraction]")
    print(f"{'='*70}")
    print(f"\nText: {text}\n")
    
    # spaCy extraction
    if SPACY_AVAILABLE:
        print(f"\n{'─'*70}")
        print(f"METHOD 1: spaCy (Fast, Free)")
        print(f"{'─'*70}")
        recognizer_spacy = EntityRecognizer(use_method="spacy")
        entities_spacy = recognizer_spacy.extract_entities(text)
        print(json.dumps(entities_spacy, indent=2))
    
    # OpenAI extraction
    if OPENAI_AVAILABLE:
        print(f"\n{'─'*70}")
        print(f"METHOD 2: OpenAI Chat API (Slower, Higher Quality, Costs $)")
        print(f"{'─'*70}")
        recognizer_openai = EntityRecognizer(use_method="openai")
        entities_openai = recognizer_openai.extract_entities(text)
        print(json.dumps(entities_openai, indent=2))
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"""
spaCy Pros:
  ✓ Fast (milliseconds)
  ✓ Free (no API costs)
  ✓ Works offline
  ✓ Good for standard NER
  
spaCy Cons:
  ✗ Limited entity types (6 types)
  ✗ No relationship extraction
  ✗ No context understanding
  ✗ Requires English model (~40MB)

OpenAI Pros:
  ✓ High quality extraction
  ✓ Understands context
  ✓ Can extract relationships
  ✓ Can extract custom entities
  
OpenAI Cons:
  ✗ Slower (~500ms per call)
  ✗ Costs money (~$0.0001 per 100 tokens)
  ✗ Requires internet
  ✗ API rate limits
    """)


if __name__ == "__main__":
    # Test entity recognition
    test_texts = [
        "Parth Kumar works as CTO at GraphRAG Corporation in Mumbai",
        "Raju is Parth's best friend and works at DRC Systems",
        "Adil met Parth in 2018 at college and they became good friends",
    ]
    
    print("\n" + "="*70)
    print("ENTITY RECOGNITION DEMO")
    print("="*70)
    
    for text in test_texts:
        recognizer = EntityRecognizer(use_method="spacy")
        recognizer.print_extracted_entities(text)
    
    # Compare methods on first text
    compare_extraction_methods(test_texts[0])
