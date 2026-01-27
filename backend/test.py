"""
Test script to run multiple queries through the browser agent and store results.
"""
import asyncio
import logging
from datetime import datetime
from browser_agent import run_browser_agent

# Set up logging
logging.basicConfig(
	level=logging.INFO,
	format='%(levelname)-8s [%(name)s] %(message)s'
)

logger = logging.getLogger(__name__)


async def test_queries():
	"""Test an array of queries and store results in text.txt."""
	
	# Array of test queries
	queries = [
  "Add a phone charger under ₹300",

  "Add a wireless mouse priced between ₹500 and ₹800 with rating above 4",

  "Add a notebook below ₹100",

  "Add a smart watch compatible with Android, rating above 4, priced under ₹3000",

  "Add a water bottle with rating 4+",

  "Add a kitchen mixer grinder with minimum 750W power and rating above 4 under ₹4000",

  "Add a men’s t-shirt size M under ₹600",

  "Add a power bank of 10000mAh under ₹1200",

  "Add a non-sponsored smartphone with at least 6GB RAM and rating above 4 under ₹15000",

  "Add a Bluetooth speaker priced below ₹1500",

  "Add a women’s running shoes size 7 with rating above 4 under ₹2500",

  "Add a USB cable under ₹200",

  "Add a headphone with noise cancellation, rating above 4, priced below ₹5000",

  "Add a book in English paperback format under ₹300",

  "Add a laptop backpack under ₹1500 with rating above 4",

  "Add a coffee mug set of 2 under ₹400",

  "Add a men’s formal shoes size 9 made of leather under ₹3500 with rating 4+",

  "Add a keyboard preferably mechanical under ₹3000",

  "Add a mobile phone cover under ₹250",

  "Add a smart TV remote compatible with Samsung under ₹600"
]

	
	results = []
	
	logger.info(f"Starting test with {len(queries)} queries...")
	
	for i, query in enumerate(queries, 1):
		logger.info(f"\n{'='*60}")
		logger.info(f"Test {i}/{len(queries)}: {query}")
		logger.info(f"{'='*60}")
		
		try:
			# Run browser agent
			result = await run_browser_agent(query, use_browser_use_llm=True)
			
			# Store result
			result_data = {
				'query': query,
				'success': result.success,
				'message': result.message,
				'product': None
			}
			
			if result.product:
				result_data['product'] = {
					'name': result.product.name,
					'price': result.product.price,
					'rating': result.product.rating,
					'url': result.product.url
				}
			
			results.append(result_data)
			
			# Log result
			if result.success:
				logger.info(f"✅ Success: {result.message}")
				if result.product:
					logger.info(f"   Product: {result.product.name}")
					logger.info(f"   Price: ₹{result.product.price}")
					logger.info(f"   Rating: {result.product.rating}")
			else:
				logger.error(f"❌ Failed: {result.message}")
		
		except Exception as e:
			logger.error(f"❌ Error processing query: {e}")
			results.append({
				'query': query,
				'success': False,
				'message': f"Error: {str(e)}",
				'product': None
			})
			import traceback
			logger.error(traceback.format_exc())
	
	# Write results to text.txt
	output_file = "text.txt"
	logger.info(f"\n{'='*60}")
	logger.info(f"Writing results to {output_file}...")
	logger.info(f"{'='*60}")
	
	with open(output_file, 'w', encoding='utf-8') as f:
		f.write("Browser Agent Test Results\n")
		f.write("="*60 + "\n")
		f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
		f.write(f"Total Queries: {len(queries)}\n")
		f.write("="*60 + "\n\n")
		
		for i, result in enumerate(results, 1):
			f.write(f"Test {i}/{len(queries)}\n")
			f.write("-" * 60 + "\n")
			f.write(f"Query: {result['query']}\n")
			f.write(f"Success: {result['success']}\n")
			f.write(f"Message: {result['message']}\n")
			
			if result['product']:
				f.write(f"\nProduct Details:\n")
				f.write(f"  Name: {result['product']['name']}\n")
				f.write(f"  Price: ₹{result['product']['price']}\n")
				f.write(f"  Rating: {result['product']['rating']}\n")
				f.write(f"  URL: {result['product']['url']}\n")
			else:
				f.write("\nNo product found.\n")
			
			f.write("\n" + "="*60 + "\n\n")
		
		# Summary
		success_count = sum(1 for r in results if r['success'])
		f.write("SUMMARY\n")
		f.write("-" * 60 + "\n")
		f.write(f"Total Tests: {len(results)}\n")
		f.write(f"Successful: {success_count}\n")
		f.write(f"Failed: {len(results) - success_count}\n")
		f.write(f"Success Rate: {(success_count/len(results)*100):.1f}%\n")
	
	logger.info(f"✅ Results written to {output_file}")
	logger.info(f"Summary: {success_count}/{len(results)} tests passed")


if __name__ == "__main__":
	try:
		asyncio.run(test_queries())
	except KeyboardInterrupt:
		logger.warning("\n\nInterrupted by user")
	except Exception as e:
		logger.error(f"\n\nError: {e}")
		import traceback
		logger.error(traceback.format_exc())
