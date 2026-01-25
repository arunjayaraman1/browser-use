"""
Example usage of the Amazon shopping automation backend.
"""
import asyncio
import logging
from intent_parser import parse_intent
from browser_agent import run_browser_agent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


async def example_simple():
    """Simple example: Add a mouse to cart."""
    logger.info("\n" + "="*60)
    logger.info("Example 1: Simple Product Search")
    logger.info("="*60)
    
    # query = "Add a wired mouse to the cart priced between ₹300 and ₹600, with user rating above 4 stars, preferably from Logitech."
    query = "Add a paperback self-help book in English with rating above 4.5 and price below ₹400."
    # query = "Add a protein bar with at least 20g protein, priced between ₹50 and ₹100 per bar, and user rating above 4."
    # query = "Add an electric kettle with minimum 1500W power, price between ₹800 and ₹1500, rating 4+, preferably from Milton."
    # query = "Add 1 kg basmati rice to the cart with rating 4+ and price below ₹200."
    # query = "Add a men’s cotton t-shirt size M, priced under ₹500, with at least 30% discount and rating above 4."
    # query = "Add a Pen under 100"

    logger.info(f"Query: {query}")
    
    # Parse intent
    logger.info("Parsing intent from query...")
    intent = parse_intent(query)
    logger.info(f"\nParsed Intent:")
    logger.info(f"  Product: {intent.product}")
    logger.info(f"  Attributes: {intent.attributes}")
    logger.info(f"  Hard Constraints: {intent.hard_constraints}")
    logger.info(f"  Soft Preferences: {intent.soft_preferences}")
    
    # Run browser agent
    logger.info("\nRunning browser agent...")
    result = await run_browser_agent(intent, use_browser_use_llm=True)
    
    # Display results
    logger.info(f"\nResult:")
    logger.info(f"  Success: {result.success}")
    logger.info(f"  Message: {result.message}")
    if result.product:
        logger.info(f"  Product: {result.product.name}")
        logger.info(f"  Price: ₹{result.product.price}")
        logger.info(f"  Rating: {result.product.rating}")
        logger.info(f"  URL: {result.product.url}")


async def example_multi_brand():
    """Example with multiple preferred brands."""
    logger.info("\n" + "="*60)
    logger.info("Example 2: Multi-Brand Search")
    logger.info("="*60)
    
    query = "electric kettle ₹800-1500, rating 4+, preferably Philips or Prestige"
    logger.info(f"Query: {query}")
    
    intent = parse_intent(query)
    logger.info(f"\nParsed Intent:")
    logger.info(f"  Product: {intent.product}")
    logger.info(f"  Soft Preferences (brands): {intent.soft_preferences.get('brands')}")
    
    result = await run_browser_agent(intent, use_browser_use_llm=True)
    
    logger.info(f"\nResult: {result.success}")
    if result.product:
        logger.info(f"  Selected: {result.product.name}")


async def example_generic():
    """Example with generic product (no specific brand)."""
    logger.info("\n" + "="*60)
    logger.info("Example 3: Generic Product Search")
    logger.info("="*60)
    
    query = "add cheapest laptop with good rating"
    logger.info(f"Query: {query}")
    
    intent = parse_intent(query)
    logger.info(f"\nParsed Intent:")
    logger.info(f"  Product: {intent.product}")
    logger.info(f"  Sort By: {intent.sort_by}")
    
    result = await run_browser_agent(intent, use_browser_use_llm=True)
    
    logger.info(f"\nResult: {result.success}")
    if result.product:
        logger.info(f"  Selected: {result.product.name} (₹{result.product.price})")


async def main():
    """Run all examples."""
    logger.info("Amazon Shopping Automation - Examples")
    logger.info("="*60)
    
    try:
        # Run examples (comment out the ones you don't want to run)
        await example_simple()
        # await example_multi_brand()
        # await example_generic()
        
    except KeyboardInterrupt:
        logger.warning("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"\n\nError: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
