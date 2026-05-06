from abc import ABC, abstractmethod
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.state import DiagnosticState  # Absolute import

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def process(self, state: DiagnosticState) -> Dict[str, Any]:
        """Process the current state and return updates"""
        pass
    
    def log_action(self, action: str):
        print(f"[{self.name}] {action}")