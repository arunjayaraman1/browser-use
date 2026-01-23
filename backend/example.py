"""
Example usage of the Amazon shopping automation backend.
"""
import asyncio
from intent_parser import parse_intent
from browser_agent import run_browser_agent


async def example_simple():
    """Simple example: Add a mouse to cart."""
    print("\n" + "="*60)
    print("Example 1: Simple Product Search")
    print("="*60)
    
    # query = "Add a wired mouse to the cart priced between ₹300 and ₹600, with user rating above 4 stars, preferably from Logitech."
    # query = "Add a paperback self-help book in English with rating above 4.5 and price below ₹400."
    # query = "Add a protein bar with at least 20g protein, priced between ₹50 and ₹100 per bar, and user rating above 4."
    # query = "Add an electric kettle with minimum 1500W power, price between ₹800 and ₹1500, rating 4+, preferably from Milton."
    # query = "Add 1 kg basmati rice to the cart with rating 4+ and price below ₹200."
    query = "Add a men’s cotton t-shirt size M, priced under ₹500, with at least 30% discount and rating above 4."


    print(f"Query: {query}")
    
    # Parse intent
    intent = parse_intent(query)
    print(f"\nParsed Intent:")
    print(f"  Product: {intent.product}")
    print(f"  Attributes: {intent.attributes}")
    print(f"  Hard Constraints: {intent.hard_constraints}")
    print(f"  Soft Preferences: {intent.soft_preferences}")
    
    # Run browser agent
    print("\nRunning browser agent...")
    result = await run_browser_agent(intent, use_browser_use_llm=True)
    
    # Display results
    print(f"\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Message: {result.message}")
    if result.product:
        print(f"  Product: {result.product.name}")
        print(f"  Price: ₹{result.product.price}")
        print(f"  Rating: {result.product.rating}")
        print(f"  URL: {result.product.url}")


async def example_multi_brand():
    """Example with multiple preferred brands."""
    print("\n" + "="*60)
    print("Example 2: Multi-Brand Search")
    print("="*60)
    
    query = "electric kettle ₹800-1500, rating 4+, preferably Philips or Prestige"
    print(f"Query: {query}")
    
    intent = parse_intent(query)
    print(f"\nParsed Intent:")
    print(f"  Product: {intent.product}")
    print(f"  Soft Preferences (brands): {intent.soft_preferences.get('brands')}")
    
    result = await run_browser_agent(intent, use_browser_use_llm=True)
    
    print(f"\nResult: {result.success}")
    if result.product:
        print(f"  Selected: {result.product.name}")


async def example_generic():
    """Example with generic product (no specific brand)."""
    print("\n" + "="*60)
    print("Example 3: Generic Product Search")
    print("="*60)
    
    query = "add cheapest laptop with good rating"
    print(f"Query: {query}")
    
    intent = parse_intent(query)
    print(f"\nParsed Intent:")
    print(f"  Product: {intent.product}")
    print(f"  Sort By: {intent.sort_by}")
    
    result = await run_browser_agent(intent, use_browser_use_llm=True)
    
    print(f"\nResult: {result.success}")
    if result.product:
        print(f"  Selected: {result.product.name} (₹{result.product.price})")


async def main():
    """Run all examples."""
    print("Amazon Shopping Automation - Examples")
    print("="*60)
    
    try:
        # Run examples (comment out the ones you don't want to run)
        await example_simple()
        # await example_multi_brand()
        # await example_generic()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
