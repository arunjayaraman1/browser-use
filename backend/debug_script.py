#!/usr/bin/env python3
"""
Debug script for examining backend code using a debugger.

This script allows you to:
- Set breakpoints and debug the browser_agent module
- Test individual functions
- Inspect variables and execution flow
- Debug the run_browser_agent function with sample data

Usage:
    # Run with Python debugger (pdb)
    python -m pdb debug_script.py
    
    # Run with IPython debugger (ipdb) - more user-friendly
    pip install ipdb
    python -m ipdb debug_script.py
    
    # Run with VS Code debugger
    # Set breakpoints in this file or backend/browser_agent.py
    # Press F5 or use "Run and Debug" panel
    
    # Run with PyCharm debugger
    # Right-click this file -> Debug 'debug_script'
"""

import asyncio
import logging
from typing import Optional

# Import backend modules
from backend.models import CartResult, ProductIntent
from backend.browser_agent import (
    run_browser_agent,
    validate_intent,
    is_sponsored,
    fix_product_url,
    build_search_query,
    build_price_slider_js,
    build_filter_instructions,
    build_selection_rules,
    is_generic_intent,
    build_product_extraction_js,
)

# Configure logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_validate_intent():
    """Test the validate_intent function."""
    print("\n=== Testing validate_intent ===")
    
    # Test valid intent
    valid_intent = ProductIntent(
        product="iPhone 15",
        hard_constraints={"price": {"min": 50000, "max": 100000}},
        soft_preferences={"brand": "Apple"}
    )
    try:
        validate_intent(valid_intent)
        print("✅ Valid intent passed validation")
    except ValueError as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test invalid intent (empty product)
    invalid_intent = ProductIntent(product="")
    try:
        validate_intent(invalid_intent)
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly caught invalid intent: {e}")
    
    # Set breakpoint here to inspect
    breakpoint()  # Python 3.7+ built-in debugger


def test_is_sponsored():
    """Test the is_sponsored function."""
    print("\n=== Testing is_sponsored ===")
    
    # Test sponsored product
    sponsored_product = {
        "title": "Test Product",
        "url": "https://amazon.in/sspa/test",
        "sponsoredLoggingUrl": "https://ad.amazon.com/track",
    }
    result = is_sponsored(sponsored_product)
    print(f"Sponsored product detected: {result}")
    
    # Test non-sponsored product
    organic_product = {
        "title": "Test Product",
        "url": "https://amazon.in/dp/B123456789",
    }
    result = is_sponsored(organic_product)
    print(f"Organic product detected: {not result}")
    
    # Set breakpoint here to inspect
    breakpoint()


def test_fix_product_url():
    """Test the fix_product_url function."""
    print("\n=== Testing fix_product_url ===")
    
    test_urls = [
        "/dp/B123456789",
        "B123456789",
        "https://amazon.in/dp/B123456789",
        "https://wrong-domain.com/dp/B123456789",
    ]
    
    for url in test_urls:
        try:
            fixed = fix_product_url(url)
            print(f"Original: {url} -> Fixed: {fixed}")
        except Exception as e:
            print(f"Error fixing {url}: {e}")
    
    # Set breakpoint here to inspect
    breakpoint()


def test_build_search_query():
    """Test the build_search_query function."""
    print("\n=== Testing build_search_query ===")
    
    intent = ProductIntent(
        product="wireless mouse",
        attributes={"color": "black", "connectivity": "bluetooth"},
        hard_constraints={"brand": "Logitech"},
        soft_preferences={"brand": "Logitech"}
    )
    
    query = build_search_query(intent)
    print(f"Search query: {query}")
    
    # Test with brand override
    query_override = build_search_query(intent, brand_override="Microsoft")
    print(f"Search query (brand override): {query_override}")
    
    # Set breakpoint here to inspect
    breakpoint()


def test_build_price_slider_js():
    """Test the build_price_slider_js function."""
    print("\n=== Testing build_price_slider_js ===")
    
    js = build_price_slider_js(min_price=5000, max_price=10000)
    if js:
        print(f"Price slider JS generated (length: {len(js)} chars)")
        print(js[:200] + "...")  # Print first 200 chars
    else:
        print("No JS generated (no price constraints)")
    
    # Set breakpoint here to inspect
    breakpoint()


def test_build_filter_instructions():
    """Test the build_filter_instructions function."""
    print("\n=== Testing build_filter_instructions ===")
    
    intent = ProductIntent(
        product="laptop",
        hard_constraints={
            "price": {"min": 30000, "max": 50000},
            "rating": {"min": 4.0},
            "discount": {"min": 10}
        }
    )
    
    price_text, rating_text, discount_text, min_price, max_price = build_filter_instructions(intent)
    print(f"Price filter: {price_text}")
    print(f"Rating filter: {rating_text}")
    print(f"Discount filter: {discount_text}")
    print(f"Min price: {min_price}, Max price: {max_price}")
    
    # Set breakpoint here to inspect
    breakpoint()


def test_build_selection_rules():
    """Test the build_selection_rules function."""
    print("\n=== Testing build_selection_rules ===")
    
    intent = ProductIntent(
        product="smartphone",
        attributes={"storage": "128GB", "ram": "8GB"},
        hard_constraints={
            "price": {"min": 20000, "max": 40000},
            "rating": {"min": 4.0},
            "brand": "Samsung"
        },
        soft_preferences={"brand": "Samsung"}
    )
    
    rules = build_selection_rules(intent, generic_mode=False)
    print("Selection rules:")
    print(rules)
    
    # Set breakpoint here to inspect
    breakpoint()


def test_is_generic_intent():
    """Test the is_generic_intent function."""
    print("\n=== Testing is_generic_intent ===")
    
    # Generic intent
    generic = ProductIntent(product="mouse")
    result = is_generic_intent(generic)
    print(f"Generic intent (mouse): {result}")
    
    # Specific intent
    specific = ProductIntent(
        product="Logitech MX Master 3S Wireless Mouse",
        hard_constraints={"brand": "Logitech"},
        attributes={"color": "black", "connectivity": "bluetooth", "dpi": "8000"}
    )
    result = is_generic_intent(specific)
    print(f"Specific intent (detailed): {not result}")
    
    # Set breakpoint here to inspect
    breakpoint()


def test_build_product_extraction_js():
    """Test the build_product_extraction_js function."""
    print("\n=== Testing build_product_extraction_js ===")
    
    js = build_product_extraction_js(min_rating=4.0)
    print(f"Product extraction JS generated (length: {len(js)} chars)")
    print(js[:300] + "...")  # Print first 300 chars
    
    # Set breakpoint here to inspect
    breakpoint()


async def test_run_browser_agent_string():
    """Test run_browser_agent with a string query."""
    print("\n=== Testing run_browser_agent with string query ===")
    
    query = "Find a wireless mouse under ₹2000 with rating above 4.0"
    
    # Set breakpoint here before running the agent
    breakpoint()
    
    try:
        result = await run_browser_agent(query, use_browser_use_llm=True)
        print(f"\nResult success: {result.success}")
        print(f"Result message: {result.message}")
        if result.product:
            print(f"Product: {result.product.name}")
            print(f"Price: ₹{result.product.price}")
    except Exception as e:
        print(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()
    
    # Set breakpoint here after running the agent
    breakpoint()


async def test_run_browser_agent_intent():
    """Test run_browser_agent with a ProductIntent object."""
    print("\n=== Testing run_browser_agent with ProductIntent ===")
    
    intent = ProductIntent(
        product="wireless mouse",
        attributes={"color": "black", "connectivity": "bluetooth"},
        hard_constraints={
            "price": {"max": 2000},
            "rating": {"min": 4.0}
        },
        soft_preferences={"brand": "Logitech"}
    )
    
    # Set breakpoint here before running the agent
    breakpoint()
    
    try:
        result = await run_browser_agent(intent, use_browser_use_llm=True)
        print(f"\nResult success: {result.success}")
        print(f"Result message: {result.message}")
        if result.product:
            print(f"Product: {result.product.name}")
            print(f"Price: ₹{result.product.price}")
    except Exception as e:
        print(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()
    
    # Set breakpoint here after running the agent
    breakpoint()


def main():
    """Main function to run debug tests."""
    print("=" * 60)
    print("Backend Debug Script")
    print("=" * 60)
    print("\nThis script allows you to debug backend functions.")
    print("Set breakpoints in this file or in backend/browser_agent.py")
    print("Use your IDE's debugger or Python's pdb/ipdb\n")
    
    # Uncomment the test functions you want to debug:
    
    # Test individual functions
    # test_validate_intent()
    # test_is_sponsored()
    # test_fix_product_url()
    # test_build_search_query()
    # test_build_price_slider_js()
    # test_build_filter_instructions()
    # test_build_selection_rules()
    # test_is_generic_intent()
    # test_build_product_extraction_js()
    
    # Test full agent (async - requires asyncio.run)
    # asyncio.run(test_run_browser_agent_string())
    # asyncio.run(test_run_browser_agent_intent())
    
    # Set a breakpoint here to start debugging
    print("\nSet breakpoints above and run with your debugger!")
    print("Or uncomment the test functions you want to debug.")
    breakpoint()


if __name__ == "__main__":
    # You can run this script in different ways:
    # 1. Direct execution: python debug_script.py
    # 2. With pdb: python -m pdb debug_script.py
    # 3. With ipdb: python -m ipdb debug_script.py
    # 4. With IDE debugger (VS Code, PyCharm, etc.)
    
    main()
