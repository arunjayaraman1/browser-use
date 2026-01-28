"""
FastAPI backend for Amazon shopping automation.
"""
import asyncio
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from models import ProductIntent, CartResult, ProductListResult
from browser_agent import run_browser_agent, run_browser_agent_list

# Set up logging
logging.basicConfig(
	level=logging.INFO,
	format='%(levelname)-8s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
	title="Amazon Shopping Automation API",
	description="API for automating Amazon shopping tasks using browser automation",
	version="1.0.0"
)

# Enable CORS for Streamlit
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # In production, specify exact origins
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Store running tasks
running_tasks: dict[str, asyncio.Task] = {}
task_results: dict[str, CartResult] = {}
list_tasks: dict[str, asyncio.Task] = {}
list_results: dict[str, ProductListResult] = {}


class RunAgentRequest(BaseModel):
	query: str = Field(..., description="Natural language product query")
	use_browser_use_llm: bool = Field(True, description="Use ChatBrowserUse LLM (recommended)")


class RunAgentResponse(BaseModel):
	task_id: str = Field(..., description="Unique task identifier")
	message: str = "Task started successfully"
	status: str = "running"


class TaskStatusResponse(BaseModel):
	task_id: str
	status: str = Field(..., description="Task status: running, completed, failed")
	result: Optional[dict] = None  # Changed to dict to support both CartResult and ProductListResult
	message: Optional[str] = None


@app.get("/health")
async def health_check():
	"""Health check endpoint."""
	return {"status": "healthy", "service": "amazon-shopping-automation"}


async def run_agent_task(task_id: str, query: str, use_browser_use_llm: bool):
	"""
	Background task to run the browser agent.
	"""
	try:
		logger.info(f"Starting browser agent task {task_id} with query: {query[:100]}...")
		result = await run_browser_agent(query, use_browser_use_llm=use_browser_use_llm)
		task_results[task_id] = result
		logger.info(f"Task {task_id} completed: success={result.success}")
	except Exception as e:
		logger.error(f"Error in task {task_id}: {e}")
		# Create error result
		task_results[task_id] = CartResult(
			success=False,
			message=f"Task failed with error: {str(e)}",
			items=[]
		)
	finally:
		# Clean up running task
		if task_id in running_tasks:
			del running_tasks[task_id]


@app.post("/run-agent", response_model=RunAgentResponse)
async def run_agent_endpoint(request: RunAgentRequest, background_tasks: BackgroundTasks):
	"""
	Start a browser automation task to add product to Amazon cart.
	
	Provide a natural language query describing what product to add to cart.
	"""
	try:
		if not request.query or not request.query.strip():
			raise HTTPException(
				status_code=400,
				detail="Query is required"
			)
		
		logger.info(f"Received query: {request.query[:100]}...")
		
		# Generate task ID
		task_id = str(uuid.uuid4())
		
		# Start background task
		task = asyncio.create_task(
			run_agent_task(task_id, request.query, request.use_browser_use_llm)
		)
		running_tasks[task_id] = task
		
		logger.info(f"Started task {task_id}")
		return RunAgentResponse(
			task_id=task_id,
			message="Browser automation task started",
			status="running"
		)
	except Exception as e:
		logger.error(f"Error starting agent task: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")


@app.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
	"""
	Get the status and result of a running or completed task.
	"""
	if task_id in running_tasks:
		# Task is still running
		return TaskStatusResponse(
			task_id=task_id,
			status="running",
			message="Task is still running"
		)
	elif task_id in task_results:
		# Task completed
		result = task_results[task_id]
		status = "completed" if result.success else "failed"
		# Convert CartResult to dict for response
		result_dict = {
			"success": result.success,
			"message": result.message,
			"items": [{"name": item.name, "price": item.price, "rating": item.rating, "url": item.url} for item in result.items],
			"product": {"name": result.product.name, "price": result.product.price, "rating": result.product.rating, "url": result.product.url} if result.product else None
		}
		return TaskStatusResponse(
			task_id=task_id,
			status=status,
			result=result_dict,
			message=result.message
		)
	else:
		raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/task/{task_id}")
async def cancel_task(task_id: str):
	"""
	Cancel a running task (if possible).
	"""
	if task_id in running_tasks:
		task = running_tasks[task_id]
		task.cancel()
		del running_tasks[task_id]
		return {"message": f"Task {task_id} cancelled", "task_id": task_id}
	else:
		raise HTTPException(status_code=404, detail=f"Task {task_id} not found or already completed")


@app.get("/tasks")
async def get_all_tasks():
	"""
	List all running and completed tasks.
	"""
	return {
		"running": list(running_tasks.keys()),
		"completed": list(task_results.keys()),
		"list_running": list(list_tasks.keys()),
		"list_completed": list(list_results.keys())
	}


async def run_list_task(task_id: str, query: str, use_browser_use_llm: bool, max_products: int = 5):
	"""
	Background task to run the browser agent for listing products.
	"""
	try:
		logger.info(f"Starting browser agent list task {task_id} with query: {query[:100]}...")
		result = await run_browser_agent_list(query, use_browser_use_llm=use_browser_use_llm, max_products=max_products)
		list_results[task_id] = result
		logger.info(f"List task {task_id} completed: success={result.success}, count={result.count}")
	except Exception as e:
		logger.error(f"Error in list task {task_id}: {e}")
		# Create error result
		list_results[task_id] = ProductListResult(
			success=False,
			message=f"Task failed with error: {str(e)}",
			products=[],
			count=0
		)
	finally:
		# Clean up running task
		if task_id in list_tasks:
			del list_tasks[task_id]


@app.post("/list-products", response_model=RunAgentResponse)
async def list_products_endpoint(request: RunAgentRequest, background_tasks: BackgroundTasks):
	"""
	Start a browser automation task to list filtered products (without adding to cart).
	
	Returns the first 5 products that match the criteria.
	"""
	try:
		if not request.query or not request.query.strip():
			raise HTTPException(
				status_code=400,
				detail="Query is required"
			)
		
		logger.info(f"Received list query: {request.query[:100]}...")
		
		# Generate task ID
		task_id = str(uuid.uuid4())
		
		# Start background task
		task = asyncio.create_task(
			run_list_task(task_id, request.query, request.use_browser_use_llm, max_products=5)
		)
		list_tasks[task_id] = task
		
		logger.info(f"Started list task {task_id}")
		return RunAgentResponse(
			task_id=task_id,
			message="Product listing task started",
			status="running"
		)
	except Exception as e:
		logger.error(f"Error starting list task: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")


@app.get("/list-task/{task_id}", response_model=TaskStatusResponse)
async def get_list_task_status(task_id: str):
	"""
	Get the status and result of a running or completed list task.
	"""
	if task_id in list_tasks:
		# Task is still running
		return TaskStatusResponse(
			task_id=task_id,
			status="running",
			message="Task is still running"
		)
	elif task_id in list_results:
		# Task completed
		result = list_results[task_id]
		status = "completed" if result.success else "failed"
		# Convert ProductListResult to dict for response
		result_dict = {
			"success": result.success,
			"message": result.message,
			"products": [{"name": p.name, "price": p.price, "rating": p.rating, "url": p.url} for p in result.products],
			"count": result.count
		}
		return TaskStatusResponse(
			task_id=task_id,
			status=status,
			result=result_dict,  # This will be serialized as JSON
			message=result.message
		)
	else:
		raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8000)
