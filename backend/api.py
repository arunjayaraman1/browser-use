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
from models import ProductIntent, CartResult
from browser_agent import run_browser_agent

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
	result: Optional[CartResult] = None
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
		return TaskStatusResponse(
			task_id=task_id,
			status=status,
			result=result,
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
async def list_tasks():
	"""
	List all running and completed tasks.
	"""
	return {
		"running": list(running_tasks.keys()),
		"completed": list(task_results.keys())
	}


if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8000)
