"""
Streamlit UI for Amazon shopping automation.
"""
import streamlit as st
import requests
import time
import json
from typing import Optional

# API configuration
API_BASE_URL = "http://localhost:8000"
STREAMLIT_PORT = 8501  # Change this if port is already in use

# Page configuration
st.set_page_config(
	page_title="Amazon Shopping Automation",
	page_icon="🛒",
	layout="wide"
)

st.title("🛒 Amazon Shopping Automation")
st.markdown("Automate adding products to your Amazon cart using natural language queries")

# Initialize session state
if "task_id" not in st.session_state:
	st.session_state.task_id = None
if "task_status" not in st.session_state:
	st.session_state.task_status = None
if "list_task_id" not in st.session_state:
	st.session_state.list_task_id = None
if "list_task_status" not in st.session_state:
	st.session_state.list_task_status = None


def check_api_health() -> bool:
	"""Check if the API is running."""
	try:
		response = requests.get(f"{API_BASE_URL}/health", timeout=2)
		return response.status_code == 200
	except Exception:
		return False


def start_agent_task(query: str) -> Optional[str]:
	"""Start a browser automation task."""
	try:
		payload = {
			"query": query,
			"use_browser_use_llm": True
		}
		
		response = requests.post(
			f"{API_BASE_URL}/run-agent",
			json=payload,
			timeout=10
		)
		response.raise_for_status()
		data = response.json()
		return data.get("task_id")
	except Exception as e:
		st.error(f"Error starting task: {str(e)}")
		return None


def start_list_task(query: str) -> Optional[str]:
	"""Start a browser automation task to list products."""
	try:
		payload = {
			"query": query,
			"use_browser_use_llm": True
		}
		
		response = requests.post(
			f"{API_BASE_URL}/list-products",
			json=payload,
			timeout=10
		)
		response.raise_for_status()
		data = response.json()
		return data.get("task_id")
	except Exception as e:
		st.error(f"Error starting list task: {str(e)}")
		return None


def get_task_status(task_id: str) -> Optional[dict]:
	"""Get the status of a running task."""
	try:
		response = requests.get(
			f"{API_BASE_URL}/task/{task_id}",
			timeout=5
		)
		response.raise_for_status()
		return response.json()
	except Exception as e:
		st.error(f"Error getting task status: {str(e)}")
		return None


def get_list_task_status(task_id: str) -> Optional[dict]:
	"""Get the status of a running list task."""
	try:
		response = requests.get(
			f"{API_BASE_URL}/list-task/{task_id}",
			timeout=5
		)
		response.raise_for_status()
		return response.json()
	except Exception as e:
		st.error(f"Error getting list task status: {str(e)}")
		return None


# Sidebar for API status
with st.sidebar:
	st.header("⚙️ Configuration")
	
	# API health check
	api_healthy = check_api_health()
	if api_healthy:
		st.success("✅ API Connected")
	else:
		st.error("❌ API Not Connected")
		st.info("Make sure the FastAPI server is running:\n```bash\nuv run python backend/api.py\n```")
	
	st.divider()
	
	# API URL configuration
	api_url = st.text_input(
		"API URL",
		value=API_BASE_URL,
		help="Base URL for the FastAPI backend"
	)
	if api_url != API_BASE_URL:
		API_BASE_URL = api_url
		st.rerun()


# Main interface
if not api_healthy:
	st.warning("⚠️ Please start the FastAPI backend server first.")
	st.code("uv run python backend/api.py", language="bash")
	st.stop()

# Query input section
st.header("📝 Product Query")

query = st.text_area(
	"Enter your product query",
	placeholder="e.g., Add an electric kettle with minimum 1500W power, price between ₹800 and ₹1500, rating 4+, preferably from Milton.",
	height=100,
	help="Describe the product you want to add to cart in natural language"
)

# Run automation section
col1, col2 = st.columns(2)

with col1:
	run_button = st.button("🚀 Run Automation", use_container_width=True, type="primary")

with col2:
	show_list_button = st.button("📋 Show List", use_container_width=True, type="secondary")

if run_button and query:
	with st.spinner("Starting browser automation..."):
		task_id = start_agent_task(query)
		if task_id:
			st.session_state.task_id = task_id
			st.session_state.task_status = "running"
			st.success(f"Task started! Task ID: {task_id}")
			st.rerun()

if show_list_button and query:
	with st.spinner("Starting product listing..."):
		task_id = start_list_task(query)
		if task_id:
			st.session_state.list_task_id = task_id
			st.session_state.list_task_status = "running"
			st.success(f"List task started! Task ID: {task_id}")
			st.rerun()


def display_result(result: dict):
	"""Display the task result."""
	st.subheader("📦 Result")
	
	success = result.get("success", False)
	message = result.get("message", "No message")
	
	if success:
		st.success(message)
		
		# Display product information
		product = result.get("product")
		items = result.get("items", [])
		
		if product:
			st.subheader("✅ Product Added to Cart")
			col1, col2, col3 = st.columns(3)
			
			with col1:
				st.write("**Name:**")
				st.write(product.get("name", "N/A"))
			
			with col2:
				st.write("**Price:**")
				price = product.get("price")
				st.write(f"₹{price}" if price else "N/A")
			
			with col3:
				st.write("**Rating:**")
				rating = product.get("rating")
				st.write(f"{rating} ⭐" if rating else "N/A")
			
			# Product URL
			url = product.get("url")
			if url:
				st.write("**Product URL:**")
				st.markdown(f"[View Product]({url})")
		
		elif items:
			st.subheader("✅ Items Added to Cart")
			for item in items:
				with st.expander(f"📦 {item.get('name', 'Unknown Product')}"):
					st.write(f"**Price:** ₹{item.get('price', 'N/A')}")
					st.write(f"**Rating:** {item.get('rating', 'N/A')} ⭐")
					url = item.get("url")
					if url:
						st.markdown(f"[View Product]({url})")
	else:
		st.error(f"❌ {message}")
	
	# Show full result JSON
	with st.expander("📄 Full Result JSON"):
		st.json(result)


def display_list_result(result: dict):
	"""Display the product list result."""
	st.subheader("📋 Product List")
	
	success = result.get("success", False)
	message = result.get("message", "No message")
	count = result.get("count", 0)
	products = result.get("products", [])
	
	if success and products:
		st.success(f"✅ {message}")
		st.info(f"Found {count} product(s) matching your criteria")
		
		# Display products in a grid
		for idx, product in enumerate(products, 1):
			with st.container():
				col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
				
				with col1:
					st.write(f"**{idx}. {product.get('name', 'Unknown Product')}**")
					url = product.get("url")
					if url:
						st.markdown(f"[🔗 View Product]({url})")
				
				with col2:
					st.write("**Price:**")
					price = product.get("price")
					st.write(f"₹{price}" if price else "N/A")
				
				with col3:
					st.write("**Rating:**")
					rating = product.get("rating")
					st.write(f"{rating} ⭐" if rating else "N/A")
				
				with col4:
					st.write("")  # Spacer
				
				st.divider()
	else:
		st.warning(f"⚠️ {message}")
		if not success:
			st.error("Failed to retrieve products. Please try again.")
	
	# Show full result JSON
	with st.expander("📄 Full Result JSON"):
		st.json(result)


# Task monitoring section
if st.session_state.task_id:
	st.header("🔄 Task Status")
	
	# Get current task status
	status_data = get_task_status(st.session_state.task_id)
	
	if status_data:
		status = status_data.get("status", "unknown")
		st.session_state.task_status = status
		
		# Display status
		if status == "running":
			st.info("🔄 Task is running...")
			st.info("💡 This may take several minutes. A browser window will open automatically.")
			st.info("💡 You can refresh this page to check the status again.")
			
			# Auto-refresh button
			if st.button("🔄 Refresh Status"):
				st.rerun()
		elif status == "completed":
			st.success("✅ Task completed successfully!")
			
			result = status_data.get("result")
			if result:
				display_result(result)
		elif status == "failed":
			st.error("❌ Task failed")
			
			result = status_data.get("result")
			if result:
				display_result(result)
	else:
		st.warning("⚠️ Could not retrieve task status. The task may have been cleared.")

# List task monitoring section
if st.session_state.list_task_id:
	st.header("📋 Product List Status")
	
	# Get current list task status
	status_data = get_list_task_status(st.session_state.list_task_id)
	
	if status_data:
		status = status_data.get("status", "unknown")
		st.session_state.list_task_status = status
		
		# Display status
		if status == "running":
			st.info("🔄 Listing products...")
			st.info("💡 This may take a minute. A browser window will open automatically.")
			st.info("💡 You can refresh this page to check the status again.")
			
			# Auto-refresh button
			if st.button("🔄 Refresh List Status"):
				st.rerun()
		elif status == "completed":
			st.success("✅ Product list completed!")
			
			result = status_data.get("result")
			if result:
				display_list_result(result)
		elif status == "failed":
			st.error("❌ List task failed")
			
			result = status_data.get("result")
			if result:
				display_list_result(result)
	else:
		st.warning("⚠️ Could not retrieve list task status. The task may have been cleared.")

# Footer
st.divider()
st.markdown(
	"""
	<div style='text-align: center; color: gray;'>
		<p>Amazon Shopping Automation | Powered by Browser-Use</p>
	</div>
	""",
	unsafe_allow_html=True
)
