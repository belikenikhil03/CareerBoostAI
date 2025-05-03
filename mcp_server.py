from fastmcp import FastMCP
from app import fetch_naukri_jobs, ask_euriai
import logging
import os
from dotenv import load_dotenv
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcp_server.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("careerboost-mcp")

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(
    name="CareerBoost AI Job Fetcher",
    description="API for fetching job listings from Naukri"
)

@mcp.tool("Fetch job listings from Naukri.com based on search keywords")
def fetch_naukri(keywords, max_jobs=60, freshness="all", experience="all"):
    """
    Fetch job listings from Naukri.com based on provided parameters.
    
    Args:
        keywords (str): Job search keywords (comma-separated)
        max_jobs (int): Maximum number of jobs to fetch
        freshness (str): Job posting timeframe
        experience (str): Experience level filter
        
    Returns:
        list: Job listings from Naukri.com
    """
    logger.info(f"Fetching Naukri jobs with keywords: {keywords}")
    try:
        start_time = time.time()
        jobs = fetch_naukri_jobs(
            search_query=keywords,
            max_jobs=max_jobs
        )
        duration = time.time() - start_time
        
        # Add additional filters that could be implemented in the future
        # This is just a placeholder for demo purposes
        if experience != "all":
            logger.info(f"Filtering by experience: {experience}")
        
        if freshness != "all":
            logger.info(f"Filtering by freshness: {freshness}")
            
        logger.info(f"Found {len(jobs)} Naukri jobs in {duration:.2f} seconds")
        return jobs
    except Exception as e:
        logger.error(f"Error fetching Naukri jobs: {str(e)}")
        return {"error": str(e)}

@mcp.tool("Extract optimal keywords from resume text for job searching")
def extract_job_keywords(resume_text):
    """
    Analyze a resume and extract optimal job search keywords.
    
    Args:
        resume_text (str): The full text of the resume
        
    Returns:
        str: Comma-separated list of job search keywords
    """
    logger.info("Extracting job keywords from resume")
    try:
        # First get a summary
        summary = ask_euriai(
            f"Summarize this resume highlighting skills, education, and experience:\n\n{resume_text}",
            max_tokens=500
        )
        
        # Then extract keywords
        keywords = ask_euriai(
            f"Based on this resume summary, suggest the best job titles/keywords for searching jobs. Give a comma-separated list only, no explanation.\n\nSummary:\n{summary}",
            max_tokens=100
        )
        
        # Clean up the response
        clean_keywords = keywords.replace("\n", "").strip()
        logger.info(f"Extracted keywords: {clean_keywords}")
        return clean_keywords
    except Exception as e:
        logger.error(f"Error extracting job keywords: {str(e)}")
        return {"error": str(e)}

@mcp.tool("Perform a complete resume analysis")
def analyze_resume(resume_text):
    """
    Perform a complete analysis of a resume.
    
    Args:
        resume_text (str): The full text of the resume
        
    Returns:
        dict: Complete resume analysis
    """
    logger.info("Performing complete resume analysis")
    try:
        start_time = time.time()
        
        # Get resume summary
        summary = ask_euriai(
            f"Summarize this resume highlighting skills, education, and experience:\n\n{resume_text}", 
            max_tokens=500
        )
        
        # Get skill gaps
        gaps = ask_euriai(
            f"Analyze this resume and highlight missing skills, certifications, or experiences needed for better job opportunities:\n\n{resume_text}", 
            max_tokens=400
        )
        
        # Get career roadmap
        roadmap = ask_euriai(
            f"Based on this resume, suggest a future roadmap to improve this person's career prospects (skills to learn, certifications needed, industry exposure):\n\n{resume_text}", 
            max_tokens=400
        )
        
        # Extract keywords
        keywords = ask_euriai(
            f"Based on this resume summary, suggest the best job titles/keywords for searching jobs. Give a comma-separated list only, no explanation.\n\nSummary:\n{summary}",
            max_tokens=100
        ).replace("\n", "").strip()
        
        # Create a structured response
        analysis = {
            "summary": summary,
            "skill_gaps": gaps,
            "career_roadmap": roadmap,
            "job_keywords": keywords,
            "analysis_timestamp": time.time()
        }
        
        duration = time.time() - start_time
        logger.info(f"Completed resume analysis in {duration:.2f} seconds")
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        return {"error": str(e)}

@mcp.tool("Get skills recommendations based on job market trends")
def get_skill_recommendations(current_skills, industry):
    """
    Get recommended skills to learn based on current skills and target industry.
    
    Args:
        current_skills (str): Comma-separated list of current skills
        industry (str): Target industry or field
        
    Returns:
        dict: Recommended skills with rationale
    """
    logger.info(f"Getting skill recommendations for industry: {industry}")
    try:
        prompt = f"""
        Based on the following current skills: {current_skills}
        
        And for someone targeting the {industry} industry,
        
        Recommend:
        1. Top 5 technical skills to learn next
        2. Top 3 soft skills to develop
        3. Any certifications that would be valuable
        4. Emerging technologies in this field to get familiar with
        
        Format your response as JSON with the keys: technical_skills, soft_skills, certifications, and emerging_technologies.
        Each should be an array of objects with 'name' and 'reason' properties.
        """
        
        response = ask_euriai(prompt, max_tokens=800)
        
        try:
            # Try to parse as JSON
            recommendations = json.loads(response)
            return recommendations
        except json.JSONDecodeError:
            # If not valid JSON, return the raw text
            logger.warning("Response was not valid JSON, returning raw text")
            return {
                "raw_response": response,
                "note": "Response could not be parsed as JSON"
            }
    except Exception as e:
        logger.error(f"Error getting skill recommendations: {str(e)}")
        return {"error": str(e)}

@mcp.tool("Generate a custom cover letter based on resume and job description")
def generate_cover_letter(resume_text, job_description, company_name):
    """
    Generate a custom cover letter based on resume and job description.
    
    Args:
        resume_text (str): The full text of the resume
        job_description (str): The job description text
        company_name (str): The name of the company
        
    Returns:
        str: Customized cover letter
    """
    logger.info(f"Generating cover letter for position at {company_name}")
    try:
        # First get a resume summary
        summary = ask_euriai(
            f"Summarize this resume highlighting skills, education, and experience that would be relevant for a job at {company_name}:\n\n{resume_text}",
            max_tokens=300
        )
        
        # Generate the cover letter
        prompt = f"""
        Create a professional cover letter for a position at {company_name}.
        
        Job Description:
        {job_description}
        
        Candidate Summary:
        {summary}
        
        The cover letter should:
        1. Be personalized to the company and role
        2. Highlight relevant skills and experience from the resume
        3. Show enthusiasm for the position
        4. Be professional but engaging
        5. Be around 250-300 words
        """
        
        cover_letter = ask_euriai(prompt, max_tokens=800)
        
        return {
            "cover_letter_text": cover_letter,
            "word_count": len(cover_letter.split()),
            "generated_timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        return {"error": str(e)}

@mcp.tool("Get server status and statistics")
def get_server_status():
    """
    Get the current server status and usage statistics.
    
    Returns:
        dict: Server status information
    """
    try:
        # This would ideally be tracking actual usage statistics
        # For now, we'll just return some placeholder info
        return {
            "status": "online",
            "uptime": time.time() - server_start_time,
            "api_calls": {
                "fetch_naukri": api_call_counts.get("fetch_naukri", 0),
                "extract_job_keywords": api_call_counts.get("extract_job_keywords", 0),
                "analyze_resume": api_call_counts.get("analyze_resume", 0),
                "get_skill_recommendations": api_call_counts.get("get_skill_recommendations", 0),
                "generate_cover_letter": api_call_counts.get("generate_cover_letter", 0)
            },
            "api_keys_status": {
                "euriai": "active" if os.getenv("EURI_API_KEY") else "missing",
                "apify": "active" if os.getenv("APIFY_API_TOKEN") else "missing"
            },
            "server_version": "1.2.0"
        }
    except Exception as e:
        logger.error(f"Error getting server status: {str(e)}")
        return {"error": str(e)}

# Initialize API call counter and server start time
api_call_counts = {}
server_start_time = time.time()

# Function to increment API call counter (used as a decorator)
def track_api_call(func):
    def wrapper(*args, **kwargs):
        # Increment the counter for this function
        func_name = func.__name__
        api_call_counts[func_name] = api_call_counts.get(func_name, 0) + 1
        return func(*args, **kwargs)
    return wrapper

# Apply the decorator to all API functions
for func_name in ["fetch_naukri", "extract_job_keywords", "analyze_resume", 
                 "get_skill_recommendations", "generate_cover_letter"]:
    if hasattr(mcp, func_name):
        setattr(mcp, func_name, track_api_call(getattr(mcp, func_name)))

if __name__ == "__main__":
    logger.info("Starting CareerBoost AI MCP Server...")
    
    # Log environment info
    api_key_status = "Available" if os.getenv("APIFY_API_TOKEN") else "Missing"
    logger.info(f"APIFY API Token: {api_key_status}")
    
    euriai_key_status = "Available" if os.getenv("EURI_API_KEY") else "Missing"
    logger.info(f"EURI API Key: {euriai_key_status}")
    
    try:
        # Start the MCP server without the port parameter
        logger.info("MCP Server starting on port 8080...")
        mcp.run()  # Removed the port parameter
    except Exception as e:
        logger.error(f"Error starting MCP server: {str(e)}")