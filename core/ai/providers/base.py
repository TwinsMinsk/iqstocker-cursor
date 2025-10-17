"""Base LLM provider classes and result models."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel


class ThemeCategorizationResult(BaseModel):
    """Result of theme categorization from LLM."""
    model_config = {"protected_namespaces": ()}
    
    themes: List[Dict[str, Any]]  # [{"theme": "Business", "confidence": 0.9, "sales": 10, "revenue": 50.0}]
    total_processed: int
    model_used: str
    processing_time_ms: int = 0


class AbstractLLMProvider(ABC):
    """Base class for all LLM providers."""
    
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
    
    @abstractmethod
    async def categorize_themes(
        self, 
        tags_by_asset: Dict[str, List[str]],  # {asset_id: [tags]}
        sales_data: Dict[str, Dict[str, float]]  # {asset_id: {"sales": X, "revenue": Y}}
    ) -> ThemeCategorizationResult:
        """
        Categorize themes from asset tags and sales data.
        
        Args:
            tags_by_asset: Dictionary mapping asset IDs to their tags
            sales_data: Dictionary mapping asset IDs to sales metrics
            
        Returns:
            ThemeCategorizationResult with categorized themes
        """
        pass
    
    @abstractmethod
    async def generate_personal_themes(
        self, 
        user_top_themes: List[str], 
        count: int = 5
    ) -> List[str]:
        """
        Generate personal themes based on user's successful themes.
        
        Args:
            user_top_themes: List of user's most successful themes
            count: Number of themes to generate
            
        Returns:
            List of generated theme names
        """
        pass
    
    def _prepare_input_data(
        self, 
        tags_by_asset: Dict[str, List[str]], 
        sales_data: Dict[str, Dict[str, float]]
    ) -> str:
        """Prepare input data for LLM prompt."""
        input_lines = []
        
        for asset_id, tags in tags_by_asset.items():
            sales_info = sales_data.get(asset_id, {"sales": 0, "revenue": 0.0})
            input_lines.append(
                f"Asset {asset_id}: {', '.join(tags)} | Sales: {sales_info['sales']}, Revenue: ${sales_info['revenue']:.2f}"
            )
        
        return "\n".join(input_lines)
