"""
Base Agent Classes

Defines the abstract base class and communication protocols for all agents
in the multi-agent compliance checking system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from langchain_openai import ChatOpenAI


class AgentMessageType(Enum):
    """Types of messages between agents."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""
    sender: str
    recipient: str
    message_type: AgentMessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


@dataclass
class AgentState:
    """Shared state structure for agent coordination."""
    session_id: str
    current_task: str
    context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    messages: List[AgentMessage] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """
    Abstract base class for all compliance checking agents.
    
    All agents inherit from this class and implement the execute method.
    Agents communicate through shared state and message passing.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        verbose: bool = False
    ):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_name: Human-readable name of the agent
            llm_model: OpenAI model name to use
            temperature: LLM temperature setting
            verbose: Enable verbose logging
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.llm_model = llm_model
        self.temperature = temperature
        self.verbose = verbose
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature
        )
        
        # Agent state
        self.state: Optional[AgentState] = None
    
    def set_state(self, state: AgentState) -> None:
        """Set the shared agent state."""
        self.state = state
    
    def get_state(self) -> Optional[AgentState]:
        """Get the current shared agent state."""
        return self.state
    
    def send_message(
        self,
        recipient: str,
        content: Dict[str, Any],
        message_type: AgentMessageType = AgentMessageType.REQUEST
    ) -> AgentMessage:
        """
        Send a message to another agent.
        
        Args:
            recipient: ID of the recipient agent
            content: Message content dictionary
            message_type: Type of message
        
        Returns:
            Created AgentMessage object
        """
        message = AgentMessage(
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            content=content
        )
        
        if self.state:
            self.state.messages.append(message)
        
        if self.verbose:
            print(f"[{self.agent_name}] → [{recipient}]: {message_type.value}")
        
        return message
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{self.agent_name}] [{level}]: {message}")
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main task.
        
        Args:
            input_data: Input data dictionary containing necessary information
        
        Returns:
            Dictionary containing the agent's output/results
        
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement execute method")
    
    def validate_input(self, input_data: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Validate that input data contains required keys.
        
        Args:
            input_data: Input data dictionary
            required_keys: List of required key names
        
        Returns:
            True if all required keys are present
        
        Raises:
            ValueError: If required keys are missing
        """
        missing_keys = [key for key in required_keys if key not in input_data]
        if missing_keys:
            raise ValueError(
                f"{self.agent_name} requires the following keys: {missing_keys}"
            )
        return True
    
    def update_state_context(self, key: str, value: Any) -> None:
        """Update a value in the shared state context."""
        if self.state:
            self.state.context[key] = value
    
    def get_state_context(self, key: str, default: Any = None) -> Any:
        """Get a value from the shared state context."""
        if self.state and key in self.state.context:
            return self.state.context[key]
        return default
    
    def store_result(self, key: str, value: Any) -> None:
        """Store a result in the shared state."""
        if self.state:
            self.state.results[key] = value
