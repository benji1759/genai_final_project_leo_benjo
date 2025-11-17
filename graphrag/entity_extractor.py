"""
Entity Extractor

Extracts regulation entities (articles, clauses, requirements) from text.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from langchain_openai import ChatOpenAI


@dataclass
class RegulationEntity:
    """Represents a regulation entity."""
    entity_type: str  # article, clause, requirement, definition
    identifier: str  # article number, clause number, etc.
    content: str
    regulation_type: Optional[str] = None  # GDPR, AI Act, etc.
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EntityExtractor:
    """
    Extracts structured entities from regulation texts.
    
    Identifies articles, clauses, requirements, and definitions
    for knowledge graph construction.
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini", use_llm: bool = True):
        """
        Initialize the entity extractor.
        
        Args:
            llm_model: LLM model for entity extraction
            use_llm: Whether to use LLM for extraction (otherwise pattern-based)
        """
        self.use_llm = use_llm
        if use_llm:
            self.llm = ChatOpenAI(model=llm_model, temperature=0)
    
    def extract_entities(
        self,
        text: str,
        regulation_type: Optional[str] = None
    ) -> List[RegulationEntity]:
        """
        Extract entities from regulation text.
        
        Args:
            text: Regulation text content
            regulation_type: Optional regulation type (GDPR, AI Act, etc.)
        
        Returns:
            List of RegulationEntity objects
        """
        if self.use_llm:
            return self._llm_extract_entities(text, regulation_type)
        else:
            return self._pattern_extract_entities(text, regulation_type)
    
    def _pattern_extract_entities(
        self,
        text: str,
        regulation_type: Optional[str] = None
    ) -> List[RegulationEntity]:
        """Pattern-based entity extraction."""
        entities = []
        
        # Extract articles
        article_pattern = r'(?i)article\s+(\d+(?:-\d+)?(?:\([a-z0-9]+\))?)'
        article_matches = re.finditer(article_pattern, text)
        
        for match in article_matches:
            article_num = match.group(1)
            # Extract content after article number (next 500 chars or to next article)
            start_pos = match.end()
            next_article = re.search(article_pattern, text[start_pos:])
            end_pos = start_pos + (next_article.start() if next_article else 500)
            
            content = text[start_pos:end_pos].strip()
            
            entities.append(RegulationEntity(
                entity_type="article",
                identifier=article_num,
                content=content,
                regulation_type=regulation_type,
                metadata={"position": match.start()}
            ))
        
        # Extract paragraphs/clauses
        paragraph_pattern = r'(?i)paragraph\s+(\d+[a-z]?)'
        para_matches = re.finditer(paragraph_pattern, text)
        
        for match in para_matches:
            para_num = match.group(1)
            start_pos = match.end()
            end_pos = min(start_pos + 200, len(text))
            
            content = text[start_pos:end_pos].strip()
            
            entities.append(RegulationEntity(
                entity_type="paragraph",
                identifier=para_num,
                content=content,
                regulation_type=regulation_type,
                metadata={"position": match.start()}
            ))
        
        return entities
    
    def _llm_extract_entities(
        self,
        text: str,
        regulation_type: Optional[str] = None
    ) -> List[RegulationEntity]:
        """LLM-based entity extraction."""
        # Use first 3000 chars for extraction (to manage token limits)
        text_sample = text[:3000]
        
        prompt = f"""
Extract regulation entities from the following text.

Regulation Type: {regulation_type or "Unknown"}

Text:
\"\"\"{text_sample}\"\"\"

Extract the following entities:
1. Articles (with article numbers)
2. Paragraphs/Clauses (with paragraph numbers)
3. Key Requirements (mandatory requirements)
4. Definitions (defined terms)

For each entity, provide:
- Type: article, paragraph, requirement, or definition
- Identifier: article/paragraph number or requirement ID
- Content: the text content of the entity

Format as JSON array:
[
  {{
    "type": "article",
    "identifier": "25",
    "content": "...",
    "regulation_type": "{regulation_type or 'Unknown'}"
  }},
  ...
]

Respond with ONLY valid JSON, no additional text.
"""
        
        try:
            response = self.llm.invoke(prompt)
            import json
            entities_data = json.loads(response.content.strip())
            
            entities = []
            for entity_data in entities_data:
                entities.append(RegulationEntity(
                    entity_type=entity_data.get("type", "unknown"),
                    identifier=entity_data.get("identifier", ""),
                    content=entity_data.get("content", ""),
                    regulation_type=entity_data.get("regulation_type", regulation_type),
                    metadata=entity_data.get("metadata", {})
                ))
            
            return entities
        except Exception as e:
            # Fallback to pattern-based
            print(f"LLM extraction failed, using pattern-based: {e}")
            return self._pattern_extract_entities(text, regulation_type)
    
    def extract_requirements(
        self,
        text: str,
        regulation_type: Optional[str] = None
    ) -> List[RegulationEntity]:
        """
        Extract specific requirements from regulation text.
        
        Args:
            text: Regulation text
            regulation_type: Optional regulation type
        
        Returns:
            List of requirement entities
        """
        # Pattern for requirements (must, shall, required)
        requirement_pattern = r'(?i)(?:must|shall|required|shall ensure)\s+([^\.]+)'
        matches = re.finditer(requirement_pattern, text)
        
        requirements = []
        for i, match in enumerate(matches, 1):
            requirement_text = match.group(1).strip()
            requirements.append(RegulationEntity(
                entity_type="requirement",
                identifier=f"req_{i}",
                content=requirement_text,
                regulation_type=regulation_type,
                metadata={"position": match.start()}
            ))
        
        return requirements
    
    def extract_definitions(
        self,
        text: str,
        regulation_type: Optional[str] = None
    ) -> List[RegulationEntity]:
        """
        Extract definitions from regulation text.
        
        Args:
            text: Regulation text
            regulation_type: Optional regulation type
        
        Returns:
            List of definition entities
        """
        # Pattern for definitions (e.g., "X means Y" or "X shall mean Y")
        definition_pattern = r'(?i)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:means|shall mean|means|refers to)\s+([^\.]+)'
        matches = re.finditer(definition_pattern, text)
        
        definitions = []
        for match in matches:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            
            definitions.append(RegulationEntity(
                entity_type="definition",
                identifier=term.lower().replace(" ", "_"),
                content=f"{term}: {definition}",
                regulation_type=regulation_type,
                metadata={"term": term, "position": match.start()}
            ))
        
        return definitions
