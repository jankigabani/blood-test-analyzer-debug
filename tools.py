## Importing libraries and files
import os
from typing import Any, Optional, Type
from dotenv import load_dotenv
load_dotenv()
from langchain_community.document_loaders import PyPDFLoader
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from crewai_tools import SerperDevTool

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool
class BloodTestReportToolSchema(BaseModel):
    """Input for BloodTestReportTool."""
    
    path: str = Field(
        default="data/sample.pdf", 
        description="Path of the PDF file containing the blood test report"
    )


class BloodTestReportTool(BaseTool):
    """A tool for reading blood test reports from PDF files.
    
    This tool reads and processes blood test report data from PDF files,
    cleaning and formatting the content for analysis.
    
    Args:
        default_path (Optional[str]): Default path to the PDF file to be read.
            If provided, this becomes the default file path for the tool.
        **kwargs: Additional keyword arguments passed to BaseTool.
    
    Example:
        >>> tool = BloodTestReportTool(default_path="data/sample.pdf")
        >>> report = tool.run()  # Reads default file
        >>> report = tool.run(path="data/other_report.pdf")  # Reads specific file
    """
    
    name: str = "Read Blood Test Report"
    description: str = "A tool that reads and processes blood test reports from PDF files. Provide a 'path' parameter with the path to the PDF file you want to read."
    args_schema: Type[BaseModel] = BloodTestReportToolSchema
    default_path: Optional[str] = None
    
    def __init__(self, default_path: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize the BloodTestReportTool.
        
        Args:
            default_path (Optional[str]): Default path to the PDF file to be read.
            **kwargs: Additional keyword arguments passed to BaseTool.
        """
        if default_path is not None:
            kwargs["description"] = (
                f"A tool that reads blood test reports from PDF files. "
                f"The default file is {default_path}, but you can provide a different 'path' parameter to read another file."
            )
        
        super().__init__(**kwargs)
        self.default_path = default_path
    
    def _run(self, path: Optional[str] = None) -> str:
        """Read data from a PDF file and return formatted blood test report.
        
        Args:
            path (Optional[str]): Path of the PDF file. Uses default_path if not provided.
        
        Returns:
            str: Full Blood Test report content, cleaned and formatted.
        """
        # Use provided path or fall back to default
        file_path = path or self.default_path or "data/sample.pdf"
        
        try:
            # Load the PDF document
            docs = PyPDFLoader(file_path=file_path).load()
            
            full_report = ""
            for data in docs:
                # Clean and format the report data
                content = data.page_content
                
                # Remove extra whitespaces and format properly
                while "\n\n" in content:
                    content = content.replace("\n\n", "\n")
                
                full_report += content + "\n"
            
            return full_report.strip()
            
        except FileNotFoundError:
            return f"Error: PDF file not found at path: {file_path}"
        except PermissionError:
            return f"Error: Permission denied when trying to read PDF file: {file_path}"
        except Exception as e:
            return f"Error: Failed to read PDF file {file_path}. {str(e)}"
    
    async def _arun(self, path: Optional[str] = None) -> str:
        """Async version of _run method."""
        # For this implementation, we'll just call the sync version
        # In a real async implementation, you'd use async PDF loading
        return self._run(path)

# ## Creating Nutrition Analysis Tool
# class NutritionTool:
#     async def analyze_nutrition_tool(blood_report_data):
#         # Process and analyze the blood report data
#         processed_data = blood_report_data
        
#         # Clean up the data format
#         i = 0
#         while i < len(processed_data):
#             if processed_data[i:i+2] == "  ":  # Remove double spaces
#                 processed_data = processed_data[:i] + processed_data[i+1:]
#             else:
#                 i += 1
                
#         # TODO: Implement nutrition analysis logic here
#         return "Nutrition analysis functionality to be implemented"

# ## Creating Exercise Planning Tool
# class ExerciseTool:
#     async def create_exercise_plan_tool(blood_report_data):        
#         # TODO: Implement exercise planning logic here
#         return "Exercise planning functionality to be implemented"

class NutritionToolSchema(BaseModel):
    """Input for NutritionTool."""
    blood_report_data: str = Field(..., description="Blood report data to analyze for nutrition")

class NutritionTool(BaseTool):
    """A tool for nutrition analysis based on blood reports."""
    
    name: str = "Nutrition Analysis Tool"
    description: str = "Analyzes blood report data and provides nutrition recommendations"
    args_schema: Type[BaseModel] = NutritionToolSchema
    
    def _run(self, blood_report_data: str) -> str:
        """Analyze nutrition based on blood report data."""
        try:
            # Process and analyze the blood report data
            processed_data = blood_report_data
            
            # Clean up the data format
            i = 0
            while i < len(processed_data):
                if processed_data[i:i+2] == "  ":  # Remove double spaces
                    processed_data = processed_data[:i] + processed_data[i+1:]
                else:
                    i += 1
                    
            # TODO: Implement nutrition analysis logic here
            return "Nutrition analysis functionality to be implemented"
        except Exception as e:
            return f"Error: Failed to analyze nutrition. {str(e)}"

## Creating Exercise Planning Tool  
class ExerciseToolSchema(BaseModel):
    """Input for ExerciseTool."""
    blood_report_data: str = Field(..., description="Blood report data to create exercise plan")

class ExerciseTool(BaseTool):
    """A tool for creating exercise plans based on blood reports."""
    
    name: str = "Exercise Planning Tool"
    description: str = "Creates exercise plans based on blood report data"
    args_schema: Type[BaseModel] = ExerciseToolSchema
    
    def _run(self, blood_report_data: str) -> str:
        """Create exercise plan based on blood report data."""
        try:
            # TODO: Implement exercise planning logic here
            return "Exercise planning functionality to be implemented"
        except Exception as e:
            return f"Error: Failed to create exercise plan. {str(e)}"