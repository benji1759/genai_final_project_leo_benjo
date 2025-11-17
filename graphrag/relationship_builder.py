"""
Relationship Builder

Builds relationships between regulation entities and policy elements.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from graphrag.entity_extractor import RegulationEntity


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    source_entity: str  # Entity identifier
    target_entity: str  # Entity identifier
    relationship_type: str  # references, implements, conflicts_with, etc.
    weight: float = 1.0  # Relationship strength
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RelationshipBuilder:
    """
    Builds relationships between regulation entities and policies.
    
    Identifies how policy elements relate to regulation articles,
    requirements, and clauses.
    """
    
    def __init__(self):
        """Initialize the relationship builder."""
        pass
    
    def build_relationships(
        self,
        policy_entities: List[Dict[str, Any]],
        regulation_entities: List[RegulationEntity]
    ) -> List[Relationship]:
        """
        Build relationships between policy and regulation entities.
        
        Args:
            policy_entities: List of policy entity dictionaries (chunks, sections)
            regulation_entities: List of regulation entities
        
        Returns:
            List of Relationship objects
        """
        relationships = []
        
        # Build entity index for quick lookup
        reg_entity_map = {ent.identifier: ent for ent in regulation_entities}
        
        # Match policy elements to regulation entities
        for policy_entity in policy_entities:
            policy_id = policy_entity.get("id", "")
            policy_content = policy_entity.get("content", "").lower()
            
            # Find related regulation entities
            for reg_entity in regulation_entities:
                reg_content = reg_entity.content.lower()
                
                # Calculate semantic similarity (simple word overlap)
                similarity = self._calculate_similarity(policy_content, reg_content)
                
                if similarity > 0.3:  # Threshold for relationship
                    relationship_type = self._determine_relationship_type(
                        policy_content,
                        reg_content,
                        similarity
                    )
                    
                    relationships.append(Relationship(
                        source_entity=policy_id,
                        target_entity=reg_entity.identifier,
                        relationship_type=relationship_type,
                        weight=similarity,
                        metadata={
                            "regulation_type": reg_entity.regulation_type,
                            "entity_type": reg_entity.entity_type
                        }
                    ))
        
        return relationships
    
    def build_citation_relationships(
        self,
        citations: List[Dict[str, Any]],
        regulation_entities: List[RegulationEntity]
    ) -> List[Relationship]:
        """
        Build relationships based on citations found in policy.
        
        Args:
            citations: List of citation dictionaries
            regulation_entities: List of regulation entities
        
        Returns:
            List of Relationship objects
        """
        relationships = []
        
        # Build entity map by identifier
        entity_map = {}
        for ent in regulation_entities:
            # Map by identifier (article number, etc.)
            entity_map[ent.identifier] = ent
            # Also map by variations (e.g., "25" and "Article 25")
            if ent.entity_type == "article":
                entity_map[f"article_{ent.identifier}"] = ent
        
        # Match citations to entities
        for citation in citations:
            citation_ref = citation.get("reference", "")
            
            # Try to find matching entity
            matching_entity = None
            
            # Direct match
            if citation_ref in entity_map:
                matching_entity = entity_map[citation_ref]
            else:
                # Extract number from citation
                import re
                num_match = re.search(r'\d+', citation_ref)
                if num_match:
                    article_num = num_match.group(0)
                    if article_num in entity_map:
                        matching_entity = entity_map[article_num]
            
            if matching_entity:
                relationships.append(Relationship(
                    source_entity="policy_document",
                    target_entity=matching_entity.identifier,
                    relationship_type="cites",
                    weight=1.0,
                    metadata={
                        "citation": citation_ref,
                        "regulation_type": matching_entity.regulation_type,
                        "citation_context": citation.get("context", "")
                    }
                ))
        
        return relationships
    
    def build_entity_hierarchy(
        self,
        regulation_entities: List[RegulationEntity]
    ) -> List[Relationship]:
        """
        Build hierarchical relationships between regulation entities.
        
        Args:
            regulation_entities: List of regulation entities
        
        Returns:
            List of hierarchical relationships
        """
        relationships = []
        
        # Group entities by regulation type
        by_regulation = {}
        for ent in regulation_entities:
            reg_type = ent.regulation_type or "Unknown"
            if reg_type not in by_regulation:
                by_regulation[reg_type] = []
            by_regulation[reg_type].append(ent)
        
        # Build article -> paragraph/clause relationships
        for reg_type, entities in by_regulation.items():
            articles = [e for e in entities if e.entity_type == "article"]
            paragraphs = [e for e in entities if e.entity_type == "paragraph"]
            
            for article in articles:
                # Find paragraphs that belong to this article
                article_num = article.identifier.split('-')[0]  # Get base number
                
                for para in paragraphs:
                    # Simple heuristic: paragraph belongs to article if content mentions it
                    if article_num in para.content or para.content in article.content:
                        relationships.append(Relationship(
                            source_entity=article.identifier,
                            target_entity=para.identifier,
                            relationship_type="contains",
                            weight=0.8,
                            metadata={
                                "regulation_type": reg_type,
                                "article_num": article_num
                            }
                        ))
        
        return relationships
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (Jaccard similarity)."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _determine_relationship_type(
        self,
        policy_content: str,
        reg_content: str,
        similarity: float
    ) -> str:
        """Determine the type of relationship."""
        # Check for conflicting language
        conflict_indicators = [
            ("prohibited", "allows"),
            ("required", "does not"),
            ("must not", "may")
        ]
        
        policy_lower = policy_content.lower()
        reg_lower = reg_content.lower()
        
        for prohibited, allowed in conflict_indicators:
            if prohibited in reg_lower and allowed in policy_lower:
                return "conflicts_with"
        
        # High similarity indicates implementation
        if similarity > 0.6:
            return "implements"
        
        # Medium similarity indicates reference
        if similarity > 0.4:
            return "references"
        
        # Low similarity might be related
        return "related_to"
