import streamlit as st
import fitz  # PyMuPDF
import os
from euriai import EuriaiClient
from dotenv import load_dotenv
from apify_client import ApifyClient
import base64
from PIL import Image
import io
import time
import random

# Load environment variables
load_dotenv()

# Initialize clients
euriai_client = EuriaiClient(
    api_key=os.getenv("EURI_API_KEY"),
    model="gpt-4.1-nano"
)

apify_client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

# Custom CSS for better UI
def load_css():
    st.markdown("""
    <style>
    /* Main theme colors and fonts */
    :root {
        --primary-color: #5C67DE;
        --secondary-color: #31304D;
        --accent-color: #F4CE14;
        --light-bg: #F9F9F9;
        --dark-bg: #1E293B;
        --text-light: #F8FAFC;
        --text-dark: #1E293B;
        --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Global styles */
    .main {
        background-color: var(--light-bg);
        color: var(--text-dark);
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        color: var(--secondary-color);
        font-weight: 700 !important;
    }
    
    /* Header styling */
    .header-container {
        background-color: var(--primary-color);
        padding: 2rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .header-container h1 {
        color: white !important;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 1.5rem;
    }
    
    /* Card styling */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--card-shadow);
        border-left: 5px solid var(--primary-color);
    }
    
    .card-title {
        color: var(--primary-color);
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    .card-title svg {
        margin-right: 0.5rem;
    }
    
    .card-content {
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* Job card styling */
    .job-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: var(--card-shadow);
        transition: transform 0.2s, box-shadow 0.2s;
        border-left: 4px solid var(--accent-color);
    }
    
    .job-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    .job-title {
        color: var(--secondary-color);
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .company-name {
        color: var(--primary-color);
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 1rem;
    }
    
    .job-meta {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
        color: #64748b;
    }
    
    .job-meta svg {
        margin-right: 0.5rem;
        flex-shrink: 0;
    }
    
    .job-apply-btn {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        cursor: pointer;
        transition: background-color 0.2s;
        text-decoration: none;
        display: inline-block;
        margin-top: 1rem;
    }
    
    .job-apply-btn:hover {
        background-color: #4A52B3;
    }
    
    /* Button styling */
    .custom-button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        cursor: pointer;
        transition: background-color 0.2s;
        width: 100%;
        margin-top: 1rem;
    }
    
    .custom-button:hover {
        background-color: #4A52B3;
    }
    
    .custom-button-secondary {
        background-color: white;
        color: var(--primary-color);
        border: 2px solid var(--primary-color);
    }
    
    .custom-button-secondary:hover {
        background-color: #f0f9ff;
    }
    
    /* Upload area styling */
    .upload-container {
        background-color: white;
        border-radius: 10px;
        padding: 2rem;
        border: 2px dashed #cbd5e1;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .upload-icon {
        font-size: 3rem;
        color: var(--primary-color);
        margin-bottom: 1rem;
    }
    
    .upload-text {
        color: #64748b;
        margin-bottom: 1rem;
    }
    
    /* Progress indicators */
    .step-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    
    .step {
        flex: 1;
        text-align: center;
        position: relative;
    }
    
    .step-number {
        background-color: #e2e8f0;
        color: #64748b;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.5rem;
        font-weight: 600;
    }
    
    .step.active .step-number {
        background-color: var(--primary-color);
        color: white;
    }
    
    .step.completed .step-number {
        background-color: #10b981;
        color: white;
    }
    
    .step-title {
        font-size: 0.875rem;
        color: #64748b;
    }
    
    .step.active .step-title {
        color: var(--primary-color);
        font-weight: 600;
    }
    
    .step.completed .step-title {
        color: #10b981;
        font-weight: 600;
    }
    
    .step-connector {
        position: absolute;
        top: 20px;
        width: 100%;
        height: 2px;
        background-color: #e2e8f0;
        left: 50%;
        z-index: -1;
    }
    
    .step.completed .step-connector {
        background-color: #10b981;
    }
    
    /* Filter controls */
    .filter-container {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--card-shadow);
    }
    
    .filter-title {
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: var(--secondary-color);
    }
    
    /* Results summary */
    .results-summary {
        background-color: #f1f5f9;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .results-number {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    
    .results-text {
        color: #64748b;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #64748b;
        font-size: 0.875rem;
    }
    
    /* Loading animation */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    }
    
    .loading-spinner {
        width: 50px;
        height: 50px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid var(--primary-color);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-text {
        color: var(--primary-color);
        font-weight: 600;
    }
    
    /* Sections */
    .section-divider {
        margin: 2rem 0;
        border-top: 1px solid #e2e8f0;
    }
    
    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
    }
    
    .section-icon {
        background-color: var(--primary-color);
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
    }
    
    /* Add more custom styles as needed */
    </style>
    """, unsafe_allow_html=True)

# Icons as SVG
def icon(name):
    icons = {
        "resume": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="18" rx="2"/><path d="M8 7h8"/><path d="M8 11h8"/><path d="M8 15h5"/></svg>""",
        "skills": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>""",
        "roadmap": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h5l2-8 4 16 2-8h5"/></svg>""",
        "location": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>""",
        "company": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>""",
        "link": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>""",
        "search": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>""",
        "upload": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>""",
        "filter": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>"""
    }
    return icons.get(name, "")

# Extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Ask EURI AI to generate output
def ask_euriai(prompt, max_tokens=500):
    response = euriai_client.generate_completion(prompt=prompt, temperature=0.5, max_tokens=max_tokens)
    if isinstance(response, dict) and 'choices' in response:
        return response['choices'][0]['message']['content']
    return response

# Fetch LinkedIn Jobs using Apify
def fetch_linkedin_jobs(search_query, location="India", rows=60):
    run_input = {
        "title": search_query,
        "location": location,
        "rows": rows,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        }
    }
    run = apify_client.actor("BHzefUZlZRKWxkTck").call(run_input=run_input)
    jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    return jobs

# Fetch Naukri Jobs using Apify
def fetch_naukri_jobs(search_query, max_jobs=60):
    run_input = {
        "keyword": search_query,
        "maxJobs": 60,
        "freshness": "all",
        "sortBy": "relevance",
        "experience": "all",
    }
    run = apify_client.actor("alpcnRV9YI9lYVPWk").call(run_input=run_input)
    jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    return jobs

# Format job cards
def render_job_card(job, source="linkedin"):
    job_title = job.get('title', 'Position')
    company = job.get('companyName', 'Company')
    location = job.get('location', '') if source == "linkedin" else job.get('location', '')
    link = job.get('link', '#') if source == "linkedin" else job.get('url', '#')
    
    html = f"""
    <div class="job-card">
        <div class="job-title">{job_title}</div>
        <div class="company-name">{company}</div>
        <div class="job-meta">
            {icon('location')} {location}
        </div>
        <a href="{link}" target="_blank" class="job-apply-btn">View Job</a>
    </div>
    """
    return html

# Animated progress bars
def progress_bar(progress, label="", detail=""):
    html = f"""
    <div style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <div style="color: #64748b; font-size: 0.875rem;">{label}</div>
            <div style="color: #64748b; font-size: 0.875rem;">{detail}</div>
        </div>
        <div style="background-color: #e2e8f0; border-radius: 10px; height: 8px; overflow: hidden;">
            <div style="background-color: var(--primary-color); height: 100%; width: {progress}%; transition: width 0.5s ease;"></div>
        </div>
    </div>
    """
    return html

# Create header
def render_header():
    return """
    <div class="header-container">
        <h1>CareerBoost AI</h1>
        <div class="header-subtitle">Upload your Resume • Get AI Analysis • Find Matching Jobs</div>
    </div>
    """

# Create custom file uploader
def custom_file_uploader():
    html = f"""
    <div class="upload-container">
        <div class="upload-icon">{icon('upload')}</div>
        <div class="upload-text">Drag and drop your resume (PDF) or click to browse</div>
    </div>
    """
    return html

# Create progress steps
def render_progress_steps(current_step):
    steps = [
        {"number": 1, "title": "Upload Resume"},
        {"number": 2, "title": "AI Analysis"},
        {"number": 3, "title": "Career Insights"},
        {"number": 4, "title": "Find Jobs"}
    ]
    
    html = '<div class="step-container">'
    
    for i, step in enumerate(steps):
        status = ""
        if step["number"] < current_step:
            status = "completed"
        elif step["number"] == current_step:
            status = "active"
            
        html += f"""
        <div class="step {status}">
            <div class="step-number">{step["number"]}</div>
            <div class="step-title">{step["title"]}</div>
            {f'<div class="step-connector"></div>' if i < len(steps) - 1 else ''}
        </div>
        """
    
    html += '</div>'
    return html

# Render loading animation
def render_loading(message="Processing..."):
    html = f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">{message}</div>
    </div>
    """
    return html

# Add a footer
def render_footer():
    return """
    <div class="footer">
        <p>© 2025 CareerBoost AI | Resume Analysis & Job Matching Platform</p>
        <p>Powered by AI to help you find the perfect career opportunity</p>
    </div>
    """

# Main Streamlit App
def main():
    st.set_page_config(page_title="CareerBoost AI - Resume Analyzer & Job Finder", layout="wide", initial_sidebar_state="collapsed")
    load_css()
    
    # Initialize session state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = None
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'gaps' not in st.session_state:
        st.session_state.gaps = None
    if 'roadmap' not in st.session_state:
        st.session_state.roadmap = None
    if 'linkedin_jobs' not in st.session_state:
        st.session_state.linkedin_jobs = []
    if 'naukri_jobs' not in st.session_state:
        st.session_state.naukri_jobs = []
    if 'search_keywords' not in st.session_state:
        st.session_state.search_keywords = ""
    
    # Render header
    st.markdown(render_header(), unsafe_allow_html=True)
    
    # Render progress steps
    st.markdown(render_progress_steps(st.session_state.current_step), unsafe_allow_html=True)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    # Step 1: Upload Resume
    if st.session_state.current_step == 1:
        with col1:
            st.markdown("<h2>Upload Your Resume</h2>", unsafe_allow_html=True)
            st.markdown("<p>Upload your resume in PDF format to get started with AI analysis and job matching.</p>", unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("", type=["pdf"], key="resume_uploader")
            
            if uploaded_file:
                with st.spinner("📚 Extracting text from resume..."):
                    st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
                    st.session_state.current_step = 2
                    st.rerun()
        
        with col2:
            st.markdown("""
            <div class="card">
                <div class="card-title">How It Works</div>
                <div class="card-content">
                    <p>1. Upload your resume (PDF format)</p>
                    <p>2. Our AI analyzes your skills & experience</p>
                    <p>3. Get personalized career insights</p>
                    <p>4. Find matching jobs from LinkedIn & Naukri</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Step 2: Analysis
    elif st.session_state.current_step == 2:
        if st.session_state.resume_text:
            st.markdown("<h2>AI Resume Analysis</h2>", unsafe_allow_html=True)
            st.markdown("<p>Our AI is analyzing your resume to provide personalized insights.</p>", unsafe_allow_html=True)
            
            with st.spinner("✍️ Summarizing Resume..."):
                st.markdown(render_loading("Analyzing resume content..."), unsafe_allow_html=True)
                st.session_state.summary = ask_euriai(f"Summarize this resume highlighting skills, education, and experience:\n\n{st.session_state.resume_text}", max_tokens=500)
            
            with st.spinner("🔎 Finding Skill Gaps..."):
                st.markdown(render_loading("Identifying skill gaps..."), unsafe_allow_html=True)
                st.session_state.gaps = ask_euriai(f"Analyze this resume and highlight missing skills, certifications, or experiences needed for better job opportunities:\n\n{st.session_state.resume_text}", max_tokens=400)
            
            with st.spinner("🚀 Creating Future Roadmap..."):
                st.markdown(render_loading("Preparing career roadmap..."), unsafe_allow_html=True)
                st.session_state.roadmap = ask_euriai(f"Based on this resume, suggest a future roadmap to improve this person's career prospects (skills to learn, certifications needed, industry exposure):\n\n{st.session_state.resume_text}", max_tokens=400)
            
            st.session_state.current_step = 3
            st.rerun()
    
    # Step 3: Results
    elif st.session_state.current_step == 3:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("<h2>Career Insights & Analysis</h2>", unsafe_allow_html=True)
            
            # Resume Summary
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{icon('resume')} Resume Summary</div>
                <div class="card-content">
                    {st.session_state.summary}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Skill Gaps
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{icon('skills')} Skill Gaps & Missing Areas</div>
                <div class="card-content">
                    {st.session_state.gaps}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Future Roadmap
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{icon('roadmap')} Future Roadmap & Preparation Strategy</div>
                <div class="card-content">
                    {st.session_state.roadmap}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Find Matching Jobs", key="find_jobs_btn"):
                st.session_state.current_step = 4
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="card">
                <div class="card-title">Next Steps</div>
                <div class="card-content">
                    <p>Review your career insights and click "Find Matching Jobs" to discover opportunities that match your profile.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add a download section
            st.markdown("""
            <div class="card">
                <div class="card-title">Download Analysis</div>
                <div class="card-content">
                    <p>Get a PDF copy of your resume analysis to review later.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Download PDF Report"):
                st.info("PDF report generation functionality will be implemented in the next version.")
                
            # Add relevant skills visualization
            st.markdown("""
            <div class="card">
                <div class="card-title">Your Skills Analysis</div>
                <div class="card-content">
                """, unsafe_allow_html=True)
            
            # Generate some demo skills with random percentages
            skills = [
                {"name": "Python", "level": 85},
                {"name": "Data Analysis", "level": 70},
                {"name": "Machine Learning", "level": 65},
                {"name": "Web Development", "level": 60},
                {"name": "SQL", "level": 75}
            ]
            
            for skill in skills:
                st.markdown(
                    progress_bar(skill["level"], skill["name"], f"{skill['level']}%"), 
                    unsafe_allow_html=True
                )
                
            st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Step 4: Job Search
    elif st.session_state.current_step == 4:
        if not st.session_state.search_keywords:
            with st.spinner("🔍 Extracting best keywords from resume..."):
                st.markdown(render_loading("Generating optimal job search keywords..."), unsafe_allow_html=True)
                keywords = ask_euriai(
                    f"Based on this resume summary, suggest the best job titles/keywords for searching jobs. Give a comma-separated list only, no explanation.\n\nSummary:\n{st.session_state.summary}",
                    max_tokens=100
                )
                st.session_state.search_keywords = keywords.replace("\n", "").strip()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("<h2>Matching Jobs</h2>", unsafe_allow_html=True)
            
            # Display search keywords and allow editing
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{icon('search')} Search Keywords</div>
                <div class="card-content">
                    <p>We've automatically generated these keywords based on your resume:</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Make the keywords editable
            # Make the keywords editable
            search_keywords_input = st.text_input("Edit keywords if needed:", value=st.session_state.search_keywords)
            
            # Search button
            if st.button("Search Jobs", key="search_jobs_btn") or not st.session_state.linkedin_jobs:
                with st.spinner("🚀 Fetching Jobs from LinkedIn and Naukri..."):
                    st.markdown(render_loading("Searching for matching jobs..."), unsafe_allow_html=True)
                    st.session_state.linkedin_jobs = fetch_linkedin_jobs(search_query=search_keywords_input, rows=60)
                    st.session_state.naukri_jobs = fetch_naukri_jobs(search_query=search_keywords_input, max_jobs=60)
            
            # Display results count
            total_jobs = len(st.session_state.linkedin_jobs) + len(st.session_state.naukri_jobs)
            st.markdown(f"""
            <div class="results-summary">
                <div class="results-number">{total_jobs}</div>
                <div class="results-text">matching jobs found</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Create tabs for LinkedIn and Naukri jobs
            linkedin_tab, naukri_tab = st.tabs(["LinkedIn Jobs (USA)", "Naukri Jobs (India)"])
            
            with linkedin_tab:
                if st.session_state.linkedin_jobs:
                    # Add filters for LinkedIn jobs
                    col_location, col_sort = st.columns(2)
                    with col_location:
                        locations = ["All Locations"] + list(set([job.get('location', '').split(',')[0].strip() for job in st.session_state.linkedin_jobs if job.get('location')]))
                        filter_location = st.selectbox("Filter by location:", locations, key="linkedin_location")
                    
                    with col_sort:
                        sort_options = ["Relevance", "Most Recent", "Company Name"]
                        sort_by = st.selectbox("Sort by:", sort_options, key="linkedin_sort")
                    
                    # Apply filters
                    filtered_jobs = st.session_state.linkedin_jobs
                    if filter_location != "All Locations":
                        filtered_jobs = [job for job in filtered_jobs if job.get('location', '').startswith(filter_location)]
                    
                    if sort_by == "Most Recent":
                        # This is a simplification, ideally you'd parse the actual date
                        # For demo, we'll just randomize
                        random.seed(42)  # Use a fixed seed for consistency
                        filtered_jobs = sorted(filtered_jobs, key=lambda x: random.random())
                    elif sort_by == "Company Name":
                        filtered_jobs = sorted(filtered_jobs, key=lambda x: x.get('companyName', '').lower())
                    
                    # Display job count
                    st.write(f"Showing {len(filtered_jobs)} LinkedIn jobs")
                    
                    for job in filtered_jobs:
                        st.markdown(render_job_card(job, source="linkedin"), unsafe_allow_html=True)
                else:
                    st.info("No LinkedIn jobs found. Try adjusting your search keywords.")
            
            with naukri_tab:
                if st.session_state.naukri_jobs:
                    # Add filters for Naukri jobs
                    col_location, col_sort = st.columns(2)
                    with col_location:
                        locations = ["All Locations"] + list(set([job.get('location', '').split(',')[0].strip() for job in st.session_state.naukri_jobs if job.get('location')]))
                        filter_location = st.selectbox("Filter by location:", locations, key="naukri_location")
                    
                    with col_sort:
                        sort_options = ["Relevance", "Most Recent", "Company Name"]
                        sort_by = st.selectbox("Sort by:", sort_options, key="naukri_sort")
                    
                    # Apply filters
                    filtered_jobs = st.session_state.naukri_jobs
                    if filter_location != "All Locations":
                        filtered_jobs = [job for job in filtered_jobs if job.get('location', '').startswith(filter_location)]
                    
                    if sort_by == "Most Recent":
                        # For demo, we'll just randomize
                        random.seed(24)  # Different seed from LinkedIn
                        filtered_jobs = sorted(filtered_jobs, key=lambda x: random.random())
                    elif sort_by == "Company Name":
                        filtered_jobs = sorted(filtered_jobs, key=lambda x: x.get('companyName', '').lower())
                    
                    # Display job count
                    st.write(f"Showing {len(filtered_jobs)} Naukri jobs")
                    
                    for job in filtered_jobs:
                        st.markdown(render_job_card(job, source="naukri"), unsafe_allow_html=True)
                else:
                    st.info("No Naukri jobs found. Try adjusting your search keywords.")
                    
        with col2:
            # Add filter section
            st.markdown("""
            <div class="card">
                <div class="card-title">Search Filters</div>
                <div class="card-content">
                    <p>Refine your job search with these filters:</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Location filter
            location_options = ["All Locations", "Remote", "USA", "India", "Europe", "Asia"]
            selected_location = st.selectbox("Location:", location_options)
            
            # Experience level filter
            experience_options = ["All Levels", "Entry Level", "Mid-Level", "Senior", "Executive"]
            selected_experience = st.selectbox("Experience Level:", experience_options)
            
            # Job type filter
            job_type_options = ["All Types", "Full-time", "Part-time", "Contract", "Internship"]
            selected_job_type = st.selectbox("Job Type:", job_type_options)
            
            # Salary range
            st.markdown("<p>Salary Range:</p>", unsafe_allow_html=True)
            salary_range = st.slider("", 0, 200, (40, 120), format="$%dk")
            
            # These filters aren't actually implemented in the demo
            st.info("Note: Filters are for demonstration only in this version.")
            
            # Add a saved jobs section
            st.markdown("""
            <div class="card">
                <div class="card-title">Saved Jobs</div>
                <div class="card-content">
                    <p>You haven't saved any jobs yet. Click "Save" on any job card to add it to your favorites.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add an application tracker
            st.markdown("""
            <div class="card">
                <div class="card-title">Application Tracker</div>
                <div class="card-content">
                    <p>Track your job applications and their status here.</p>
                    <p>Premium feature coming soon!</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    
    # Add footer at the end
    st.markdown(render_footer(), unsafe_allow_html=True)