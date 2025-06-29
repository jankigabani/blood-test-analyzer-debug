from celery import current_task
from celery_app import celery_app
import os
import uuid
from typing import Dict, Any

# Import your modules directly instead of importing from main
from crewai import Crew, Process
from agents import doctor
from task import help_patients


def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """To run the whole crew - Duplicated here to avoid circular import"""
    medical_crew = Crew(
        agents=[doctor],
        tasks=[help_patients],
        process=Process.sequential,
    )
    
    result = medical_crew.kickoff({'query': query, 'file_path': file_path})
    return result


@celery_app.task(bind=True, name="analyze_blood_report_async")
def analyze_blood_report_task(self, query: str, file_path: str, original_filename: str) -> Dict[str, Any]:
    """
    Celery task to analyze blood report asynchronously
    """
    try:
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Processing blood report...', 'progress': 25}
        )
        
        # Run your existing crew analysis
        result = run_crew(query=query, file_path=file_path)
        
        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Analysis complete, formatting results...', 'progress': 90}
        )
        
        return {
            'status': 'SUCCESS',
            'query': query,
            'analysis': str(result),
            'file_processed': original_filename,
            'task_id': self.request.id
        }
        
    except Exception as e:
        # Update task state on failure
        self.update_state(
            state='FAILURE',
            meta={'status': f'Error: {str(e)}', 'progress': 0}
        )
        raise


@celery_app.task(bind=True, name="cleanup_file")
def cleanup_file_task(self, file_path: str):
    """
    Celery task to cleanup uploaded files after processing
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"status": "File cleaned up successfully"}
        return {"status": "File not found"}
    except Exception as e:
        return {"status": f"Cleanup failed: {str(e)}"}