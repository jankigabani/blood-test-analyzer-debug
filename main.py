from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import uuid
import redis
from typing import Dict, Any

from crewai import Crew, Process
from agents import doctor
from task import help_patients
from celery_app import celery_app

app = FastAPI(title="Blood Test Report Analyser with Queue")

# Redis client for status tracking
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Keep your existing run_crew function unchanged
def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """To run the whole crew - UNCHANGED"""
    medical_crew = Crew(
        agents=[doctor],
        tasks=[help_patients],
        process=Process.sequential,
    )
    
    result = medical_crew.kickoff({'query': query, 'file_path': file_path})
    return result


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Blood Test Report Analyser API with Queue is running",
        "queue_status": "Available",
        "endpoints": {
            "analyze": "POST /analyze - Queue analysis job",
            "status": "GET /status/{task_id} - Check job status",
            "result": "GET /result/{task_id} - Get analysis result"
        }
    }


@app.post("/analyze")
async def analyze_blood_report(
    file: UploadFile = File(...),
    query: str = Form(default="Summarise my Blood Test Report")
):
    """Queue blood test report analysis"""
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = f"data/blood_test_report_{file_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validate query
        if query == "" or query is None:
            query = "Summarise my Blood Test Report"
        
        # Import tasks here to avoid circular import
        from tasks.worker_tasks import analyze_blood_report_task, cleanup_file_task
        
        # Queue the analysis task
        task = analyze_blood_report_task.delay(
            query=query.strip(),
            file_path=file_path,
            original_filename=file.filename
        )
        
        # Schedule file cleanup for later
        cleanup_file_task.apply_async(args=[file_path], countdown=3600)  # Cleanup after 1 hour
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "Analysis job queued successfully",
            "check_status_url": f"/status/{task.id}",
            "get_result_url": f"/result/{task.id}"
        }
        
    except Exception as e:
        # Cleanup on immediate failure
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error queuing analysis: {str(e)}")


@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a queued analysis task"""
    try:
        # Import here to avoid circular import
        from tasks.worker_tasks import analyze_blood_report_task
        
        task = analyze_blood_report_task.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task is waiting in queue...',
                'progress': 0
            }
        elif task.state == 'PROCESSING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': task.info.get('status', 'Processing...'),
                'progress': task.info.get('progress', 0)
            }
        elif task.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Analysis completed successfully',
                'progress': 100,
                'result_available': True
            }
        elif task.state == 'FAILURE':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': str(task.info),
                'progress': 0,
                'error': True
            }
        else:
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Unknown state',
                'progress': 0
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task not found: {str(e)}")


@app.get("/result/{task_id}")
async def get_task_result(task_id: str):
    """Get the result of a completed analysis task"""
    try:
        # Import here to avoid circular import
        from tasks.worker_tasks import analyze_blood_report_task
        
        task = analyze_blood_report_task.AsyncResult(task_id)
        
        if task.state == 'SUCCESS':
            return task.result
        elif task.state == 'FAILURE':
            raise HTTPException(status_code=400, detail="Task failed")
        elif task.state == 'PENDING':
            raise HTTPException(status_code=202, detail="Task is still pending")
        else:
            raise HTTPException(status_code=202, detail="Task is still processing")
            
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task not found: {str(e)}")


@app.get("/queue/stats")
async def get_queue_stats():
    """Get queue statistics"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        
        return {
            "queue_length": len(active) if active else 0,
            "worker_stats": stats,
            "active_tasks": active
        }
    except Exception as e:
        return {"error": f"Could not get queue stats: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)