"""
Pydantic models for Amazon shopping automation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ProductIntent(BaseModel):
    """
    Flexible product intent that supports dynamic attributes and preferences.
    
    Core structure:
    - product: Main product name (required)
    - attributes: Product characteristics (color, size, material, connectivity, etc.)
    - hard_constraints: Must satisfy (price ranges, ratings, specific features,discount percentage)
    - soft_preferences: Nice to have, used for sorting/preference (preferred brands, features)
    - sort_by: Explicit sorting preference
    """
    # Core field - always present
    product: str = Field(..., description="Main product name with brand and model if available")
    
    # Flexible containers for dynamic attributes
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Product characteristics like color, size, connectivity, material, etc."
    )
    
    hard_constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Must-have requirements like price range, min rating, specific features, discount percentage"
    )
    
    soft_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Preferred but not required - brand preferences, feature preferences"
    )
    
    # Common fields for convenience (can also be in hard_constraints)
    sort_by: Optional[str] = Field(
        None,
        description="Sorting preference: price_asc, price_desc, rating_asc, rating_desc"
    )
    
    # Legacy compatibility helpers (derived from hard_constraints/attributes)
    @property
    def min_price(self) -> Optional[float]:
        return self.hard_constraints.get('price', {}).get('min')
    
    @property
    def max_price(self) -> Optional[float]:
        return self.hard_constraints.get('price', {}).get('max')
    
    @property
    def min_rating(self) -> Optional[float]:
        return self.hard_constraints.get('rating', {}).get('min')
    
    @property
    def max_rating(self) -> Optional[float]:
        return self.hard_constraints.get('rating', {}).get('max')
    
    @property
    def color(self) -> Optional[str]:
        return self.attributes.get('color')
    
    @property
    def brand(self) -> Optional[str]:
        # Check both hard constraints and soft preferences
        hard_brand = self.hard_constraints.get('brand')
        if hard_brand:
            return hard_brand
        
        # Check single soft brand
        soft_brand = self.soft_preferences.get('brand')
        if soft_brand:
            return soft_brand
        
        # Check multiple soft brands (return first one for compatibility)
        soft_brands = self.soft_preferences.get('brands')
        if soft_brands and isinstance(soft_brands, list) and soft_brands:
            return soft_brands[0]
        
        return None


class ProductItem(BaseModel):
    """Represents a product item in the cart."""
    name: str
    price: Optional[float] = None
    rating: Optional[float] = None
    url: str


class CartResult(BaseModel):
    """Result of adding product to cart."""
    items: List[ProductItem] = Field(default_factory=list)
    success: bool = Field(default=True, description="Whether the operation was successful")
    message: Optional[str] = Field(default=None, description="Optional message about the result")
    product: Optional[ProductItem] = Field(default=None, description="The product that was added to cart")
