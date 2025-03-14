"""
Base model interface for AI code review.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """Base class for AI models used for code review."""
    
    @abstractmethod
    def __init__(self, model_name: str, **kwargs):
        """Initialize the model.
        
        Args:
            model_name: Name of the model to use
            **kwargs: Additional model-specific parameters
        """
        self.model_name = model_name
    
    @abstractmethod
    async def analyze_code(
        self, 
        code: str, 
        filename: str, 
        context: Optional[Dict] = None
    ) -> Dict:
        """Analyze code and provide feedback.
        
        Args:
            code: Code content to analyze
            filename: Name of the file being analyzed
            context: Additional context for the analysis
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    @abstractmethod
    async def analyze_diff(
        self, 
        diff: str, 
        filename: str, 
        context: Optional[Dict] = None
    ) -> Dict:
        """Analyze a diff and provide feedback.
        
        Args:
            diff: Diff content to analyze
            filename: Name of the file being analyzed
            context: Additional context for the analysis
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    @abstractmethod
    async def summarize_review(
        self, 
        file_reviews: List[Dict], 
        pr_description: Optional[str] = None
    ) -> str:
        """Summarize the review of multiple files.
        
        Args:
            file_reviews: List of file review results
            pr_description: Description of the pull request
            
        Returns:
            Summary of the review
        """
        pass 