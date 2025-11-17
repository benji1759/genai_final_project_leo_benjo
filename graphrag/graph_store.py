"""
Graph Store

Stores and manages knowledge graph of regulation entities and relationships.
"""

import json
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from dataclasses import asdict

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from graphrag.entity_extractor import RegulationEntity
from graphrag.relationship_builder import Relationship


class GraphStore:
    """
    Stores knowledge graph of regulation entities and relationships.
    
    Can use NetworkX for complex graph operations or simple JSON for basic storage.
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        use_networkx: bool = True
    ):
        """
        Initialize the graph store.
        
        Args:
            storage_path: Path to store graph data (JSON file)
            use_networkx: Whether to use NetworkX for graph operations
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.use_networkx = use_networkx and NETWORKX_AVAILABLE
        
        if self.use_networkx:
            self.graph = nx.DiGraph()
        else:
            self.entities: Dict[str, Dict[str, Any]] = {}
            self.relationships: List[Dict[str, Any]] = []
    
    def add_entity(self, entity: RegulationEntity) -> None:
        """
        Add a regulation entity to the graph.
        
        Args:
            entity: RegulationEntity to add
        """
        entity_id = f"{entity.regulation_type}_{entity.entity_type}_{entity.identifier}" if entity.regulation_type else f"{entity.entity_type}_{entity.identifier}"
        
        entity_data = {
            "id": entity_id,
            "type": entity.entity_type,
            "identifier": entity.identifier,
            "content": entity.content,
            "regulation_type": entity.regulation_type,
            "metadata": entity.metadata
        }
        
        if self.use_networkx:
            self.graph.add_node(entity_id, **entity_data)
        else:
            self.entities[entity_id] = entity_data
    
    def add_relationship(self, relationship: Relationship) -> None:
        """
        Add a relationship to the graph.
        
        Args:
            relationship: Relationship to add
        """
        source_id = relationship.source_entity
        target_id = relationship.target_entity
        
        # Ensure nodes exist
        if not self.use_networkx:
            if source_id not in self.entities:
                self.entities[source_id] = {"id": source_id, "type": "unknown"}
            if target_id not in self.entities:
                self.entities[target_id] = {"id": target_id, "type": "unknown"}
        
        rel_data = {
            "type": relationship.relationship_type,
            "weight": relationship.weight,
            "metadata": relationship.metadata
        }
        
        if self.use_networkx:
            self.graph.add_edge(source_id, target_id, **rel_data)
        else:
            self.relationships.append({
                "source": source_id,
                "target": target_id,
                **rel_data
            })
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            Entity data dictionary or None
        """
        if self.use_networkx:
            if entity_id in self.graph:
                return dict(self.graph.nodes[entity_id])
            return None
        else:
            return self.entities.get(entity_id)
    
    def get_related_entities(
        self,
        entity_id: str,
        relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get entities related to the given entity.
        
        Args:
            entity_id: Entity identifier
            relationship_type: Optional filter by relationship type
        
        Returns:
            List of related entity dictionaries
        """
        related = []
        
        if self.use_networkx:
            if entity_id not in self.graph:
                return related
            
            # Get neighbors
            for neighbor_id in self.graph.neighbors(entity_id):
                edge_data = self.graph[entity_id][neighbor_id]
                
                if relationship_type is None or edge_data.get("type") == relationship_type:
                    neighbor_data = dict(self.graph.nodes[neighbor_id])
                    neighbor_data["relationship"] = edge_data.get("type", "")
                    related.append(neighbor_data)
        else:
            # Filter relationships
            for rel in self.relationships:
                if rel["source"] == entity_id:
                    if relationship_type is None or rel["type"] == relationship_type:
                        target_id = rel["target"]
                        target_entity = self.entities.get(target_id, {"id": target_id})
                        target_entity["relationship"] = rel["type"]
                        related.append(target_entity)
        
        return related
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 3
    ) -> Optional[List[str]]:
        """
        Find path between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_length: Maximum path length
        
        Returns:
            List of entity IDs forming the path, or None
        """
        if self.use_networkx:
            try:
                if source_id not in self.graph or target_id not in self.graph:
                    return None
                
                # Try to find shortest path
                path = nx.shortest_path(self.graph, source_id, target_id)
                
                if len(path) <= max_length + 1:
                    return path
            except nx.NetworkXNoPath:
                return None
        
        return None
    
    def get_entities_by_type(
        self,
        entity_type: str,
        regulation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all entities of a specific type.
        
        Args:
            entity_type: Type of entity (article, paragraph, etc.)
            regulation_type: Optional filter by regulation type
        
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        if self.use_networkx:
            for node_id, node_data in self.graph.nodes(data=True):
                if node_data.get("type") == entity_type:
                    if regulation_type is None or node_data.get("regulation_type") == regulation_type:
                        entities.append(dict(node_data))
        else:
            for entity_id, entity_data in self.entities.items():
                if entity_data.get("type") == entity_type:
                    if regulation_type is None or entity_data.get("regulation_type") == regulation_type:
                        entities.append(entity_data)
        
        return entities
    
    def save(self, file_path: Optional[str] = None) -> None:
        """
        Save graph to file.
        
        Args:
            file_path: Optional file path (uses storage_path if not provided)
        """
        save_path = Path(file_path) if file_path else self.storage_path
        
        if save_path is None:
            raise ValueError("No storage path specified")
        
        if self.use_networkx:
            # Convert NetworkX graph to JSON-serializable format
            data = {
                "nodes": [
                    {"id": node_id, **data}
                    for node_id, data in self.graph.nodes(data=True)
                ],
                "edges": [
                    {"source": source, "target": target, **data}
                    for source, target, data in self.graph.edges(data=True)
                ]
            }
        else:
            data = {
                "nodes": list(self.entities.values()),
                "edges": self.relationships
            }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self, file_path: Optional[str] = None) -> None:
        """
        Load graph from file.
        
        Args:
            file_path: Optional file path (uses storage_path if not provided)
        """
        load_path = Path(file_path) if file_path else self.storage_path
        
        if load_path is None or not load_path.exists():
            return
        
        with open(load_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if self.use_networkx:
            self.graph.clear()
            
            # Add nodes
            for node_data in data.get("nodes", []):
                node_id = node_data.pop("id")
                self.graph.add_node(node_id, **node_data)
            
            # Add edges
            for edge_data in data.get("edges", []):
                source = edge_data.pop("source")
                target = edge_data.pop("target")
                self.graph.add_edge(source, target, **edge_data)
        else:
            # Load into simple structure
            self.entities = {node["id"]: node for node in data.get("nodes", [])}
            self.relationships = data.get("edges", [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        if self.use_networkx:
            return {
                "num_nodes": self.graph.number_of_nodes(),
                "num_edges": self.graph.number_of_edges(),
                "num_components": nx.number_weakly_connected_components(self.graph) if self.graph else 0
            }
        else:
            return {
                "num_nodes": len(self.entities),
                "num_edges": len(self.relationships)
            }
