"""
OpenAI model implementation for code review.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Union

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

from pr_agent.models.base import BaseModel

logger = logging.getLogger(__name__)

# Default prompts
CODE_ANALYSIS_PROMPT = """
You are an expert code reviewer. Analyze the following code and provide feedback.

File: {filename}

```
{code}
```

Provide a detailed analysis including:
1. Code quality issues
2. Potential bugs or edge cases
3. Performance concerns
4. Security vulnerabilities
5. Suggestions for improvement

Format your response as a JSON object with the following structure:
{
  "issues": [
    {
      "type": "bug|security|performance|style|other",
      "severity": "high|medium|low",
      "description": "Detailed description of the issue",
      "suggestion": "Suggested fix or improvement"
    }
  ],
  "summary": "Overall summary of the code quality"
}
"""

DIFF_ANALYSIS_PROMPT = """
You are an expert code reviewer. Analyze the following diff and provide feedback.

File: {filename}

```diff
{diff}
```

Provide a detailed analysis including:
1. Code quality issues in the changes
2. Potential bugs or edge cases introduced
3. Performance impacts
4. Security concerns
5. Suggestions for improvement

Format your response as a JSON object with the following structure:
{
  "issues": [
    {
      "type": "bug|security|performance|style|other",
      "severity": "high|medium|low",
      "description": "Detailed description of the issue",
      "suggestion": "Suggested fix or improvement",
      "line": "Line number or range if applicable"
    }
  ],
  "summary": "Overall assessment of the changes"
}
"""

REVIEW_SUMMARY_PROMPT = """
You are an expert code reviewer. Summarize the following file reviews into an overall pull request review.

Pull Request Description:
{pr_description}

File Reviews:
{file_reviews}

Provide a comprehensive summary of the review, including:
1. Overall assessment of the changes
2. Major issues that need to be addressed
3. Minor issues that could be improved
4. Positive aspects of the changes
5. Suggestions for future improvements

Your summary should be constructive, specific, and actionable.
"""


class OpenAIModel(BaseModel):
    """OpenAI model implementation for code review."""
    
    def __init__(
        self, 
        model_name: str = None, 
        api_key: str = None, 
        temperature: float = 0.0,
        **kwargs
    ):
        """Initialize the OpenAI model.
        
        Args:
            model_name: Name of the OpenAI model to use
            api_key: OpenAI API key
            temperature: Temperature for model generation
            **kwargs: Additional model-specific parameters
        """
        super().__init__(model_name=model_name or os.getenv("MODEL_NAME", "gpt-4-turbo"))
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not set in environment")
        
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
            **kwargs
        )
        logger.debug(f"Initialized OpenAI model {self.model_name}")
    
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
        prompt = ChatPromptTemplate.from_template(CODE_ANALYSIS_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        result = await chain.ainvoke({"code": code, "filename": filename})
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.error("Failed to parse model response as JSON")
            return {
                "issues": [],
                "summary": "Error: Failed to parse model response"
            }
    
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
        prompt = ChatPromptTemplate.from_template(DIFF_ANALYSIS_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        result = await chain.ainvoke({"diff": diff, "filename": filename})
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.error("Failed to parse model response as JSON")
            return {
                "issues": [],
                "summary": "Error: Failed to parse model response"
            }
    
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
        prompt = ChatPromptTemplate.from_template(REVIEW_SUMMARY_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        file_reviews_str = json.dumps(file_reviews, indent=2)
        
        result = await chain.ainvoke({
            "file_reviews": file_reviews_str,
            "pr_description": pr_description or "No description provided"
        })
        
        return result 