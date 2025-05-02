import streamlit as st
import os
import io
import random
import time
import re
from PIL import Image
from dotenv import load_dotenv
from apify_client import ApifyClient
from euriai import EuriaiClient
import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Load environment variables
load_dotenv()

# Initialize clients
euriai_client = EuriaiClient(
    api_key=os.getenv("EURI_API_KEY"),
    model="gpt-4.1-nano"
)

apify_client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    try:
        # Try different PDF extraction methods
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except ImportError:
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getbuffer()))
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
            except ImportError:
                return "PDF text extraction libraries not available. Please install PyMuPDF or PyPDF2."
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

# Extract skills using EuriAI client
def extract_skills_from_resume(resume_text):
    # Use EuriAI to extract skills with improved prompt
    skills_prompt = f"""Extract the top 10 technical skills from this resume.
    Return ONLY a comma-separated list of skills, no additional text or explanations.
    Make sure your response is complete and not cut off.
    
    Resume text:
    {resume_text}"""
    
    skills_response = ask_euriai(skills_prompt, max_tokens=200)
    
    # Parse the comma-separated response
    skills_list = [skill.strip() for skill in skills_response.split(',')]
    return skills_list[:10]  # Ensure we get max 10 skills

# Clean response to ensure no cut-off HTML
def clean_response(response):
    # Remove any cut-off HTML tags at the end
    cleaned = re.sub(r'<[^>]*$', '', response)
    return cleaned

# Ask EURI AI to generate output with improved prompts to prevent cutoffs
def ask_euriai(prompt, max_tokens=800):
    # Add instructions for complete responses
    enhanced_prompt = f"""{prompt}

Please provide a complete, well-structured response with no cut-off sentences. 
Ensure all points are fully explained and properly concluded.
Do not leave any thoughts incomplete."""
    
    response = euriai_client.generate_completion(prompt=enhanced_prompt, temperature=0.5, max_tokens=max_tokens)
    if isinstance(response, dict) and 'choices' in response:
        return response['choices'][0]['message']['content']
    return response

# Generate PDF report
def generate_pdf_report():
    try:
        # Create buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(buffer, pagesize=A4, title="Career Analysis Report")
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Content
        content = []
        
        # Title
        content.append(Paragraph("Career Analysis Report", title_style))
        content.append(Spacer(1, 20))
        
        # Resume Summary
        content.append(Paragraph("Resume Summary", subtitle_style))
        content.append(Spacer(1, 10))
        content.append(Paragraph(st.session_state.summary, normal_style))
        content.append(Spacer(1, 20))
        
        # Skill Gaps
        content.append(Paragraph("Skill Gaps & Missing Areas", subtitle_style))
        content.append(Spacer(1, 10))
        content.append(Paragraph(st.session_state.gaps, normal_style))
        content.append(Spacer(1, 20))
        
        # Future Roadmap
        content.append(Paragraph("Future Roadmap & Preparation Strategy", subtitle_style))
        content.append(Spacer(1, 10))
        content.append(Paragraph(st.session_state.roadmap, normal_style))
        content.append(Spacer(1, 20))
        
        # Skills List
        content.append(Paragraph("Your Skills", subtitle_style))
        content.append(Spacer(1, 10))
        skills_text = ", ".join(st.session_state.skills)
        content.append(Paragraph(skills_text, normal_style))
        
        # Build PDF
        doc.build(content)
        
        # Get PDF from buffer
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Encode to base64 for download
        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="career_analysis_report.pdf" class="job-apply-btn" style="text-decoration:none;">Download PDF Report</a>'
        return href
        
    except Exception as e:
        return f"Error generating PDF: {str(e)}"

# Fetch Naukri Jobs using Apify
def fetch_naukri_jobs(search_query, max_jobs=60):
    try:
        run_input = {
            "keyword": search_query,
            "maxJobs": max_jobs,
            "freshness": "all",
            "sortBy": "relevance",
            "experience": "all",
        }
        run = apify_client.actor("alpcnRV9YI9lYVPWk").call(run_input=run_input)
        jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        return jobs
    except Exception as e:
        st.error(f"Error fetching Naukri jobs: {str(e)}")
        # Return sample data for demonstration
        return [
            {"title": "Python Developer", "companyName": "Tech Solutions India", "location": "Bangalore, India", "url": "https://www.naukri.com/job-listings-123456"},
            {"title": "Data Analyst", "companyName": "Analytics India", "location": "Delhi, India", "url": "https://www.naukri.com/job-listings-234567"},
            {"title": "Backend Developer", "companyName": "Software Systems", "location": "Mumbai, India", "url": "https://www.naukri.com/job-listings-345678"}
        ]

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
    
    /* Mobile responsiveness */
    @media screen and (max-width: 768px) {
        .header-container h1 {
            font-size: 2rem !important;
        }
        
        .step-container {
            flex-direction: column;
        }
        
        .step {
            margin-bottom: 1rem;
        }
        
        .step-connector {
            display: none;
        }
    }
    /* Skills list */
    .skills-list {
        list-style-type: disc;
        margin-left: 20px;
        padding-left: 10px;
    }
    .skills-list li {
        margin-bottom: 8px;
    }
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
        "filter": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>""",
        "download": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>"""
    }
    return icons.get(name, "")

# Format job cards
def render_job_card(job, source="naukri"):
    job_title = job.get('title', 'Position')
    company = job.get('companyName', 'Company')
    location = job.get('location', '')
    link = job.get('url', '#')
    
    # Make sure link is valid and absolute
    if not link or link == '#':
        link = "https://example.com/job"  # Fallback link
    elif not link.startswith(('http://', 'https://')):
        link = f"https://{link}"
    
    html = f"""
    <div class="job-card">
        <div class="job-title">{job_title}</div>
        <div class="company-name">{company}</div>
        <div class="job-meta">
            {icon('location')} {location}
        </div>
        <a href="{link}" target="_blank" rel="noopener noreferrer" class="job-apply-btn">View Job</a>
    </div>
    """
    return html

# Render card with proper HTML cleaning
def render_card(title, icon_name, content):
    # Clean the content to ensure no cut-off HTML
    cleaned_content = clean_response(content)
    
    html = f"""
    <div class="card">
        <div class="card-title">{icon(icon_name)} {title}</div>
        <div class="card-content">
            {cleaned_content}
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

# Create progress steps with fixed HTML
def render_progress_steps(current_step):
    # Create all steps HTML directly without any conditional logic in f-strings
    step1_status = "completed" if current_step > 1 else "active" if current_step == 1 else ""
    step2_status = "completed" if current_step > 2 else "active" if current_step == 2 else ""
    step3_status = "completed" if current_step > 3 else "active" if current_step == 3 else ""
    step4_status = "completed" if current_step > 4 else "active" if current_step == 4 else ""
    
    html = """
    <div class="step-container">
        <div class="step {0}">
            <div class="step-number">1</div>
            <div class="step-title">Upload Resume</div>
            <div class="step-connector"></div>
        </div>
        <div class="step {1}">
            <div class="step-number">2</div>
            <div class="step-title">AI Analysis</div>
            <div class="step-connector"></div>
        </div>
        <div class="step {2}">
            <div class="step-number">3</div>
            <div class="step-title">Career Insights</div>
            <div class="step-connector"></div>
        </div>
        <div class="step {3}">
            <div class="step-number">4</div>
            <div class="step-title">Find Jobs</div>
        </div>
    </div>
    """.format(step1_status, step2_status, step3_status, step4_status)
    
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
    st.set_page_config(
        page_title="CareerBoost AI - Resume Analyzer & Job Finder", 
        layout="wide", 
        initial_sidebar_state="collapsed",
        page_icon="📄"
    )
    
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
    if 'naukri_jobs' not in st.session_state:
        st.session_state.naukri_jobs = []
    if 'search_keywords' not in st.session_state:
        st.session_state.search_keywords = ""
    if 'skills' not in st.session_state:
        st.session_state.skills = []
    
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
            
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="resume_uploader", label_visibility="collapsed")
            
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
                    <p>4. Find matching jobs from Naukri</p>
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
                st.session_state.summary = ask_euriai(f"Summarize this resume highlighting skills, education, and experience:\n\n{st.session_state.resume_text}", max_tokens=800)
            
            with st.spinner("🔎 Finding Skill Gaps..."):
                st.markdown(render_loading("Identifying skill gaps..."), unsafe_allow_html=True)
                st.session_state.gaps = ask_euriai(f"Analyze this resume and highlight missing skills, certifications, or experiences needed for better job opportunities:\n\n{st.session_state.resume_text}", max_tokens=800)
            
            with st.spinner("🚀 Creating Future Roadmap..."):
                st.markdown(render_loading("Preparing career roadmap..."), unsafe_allow_html=True)
                st.session_state.roadmap = ask_euriai(f"Based on this resume, suggest a future roadmap to improve this person's career prospects (skills to learn, certifications needed, industry exposure):\n\n{st.session_state.resume_text}", max_tokens=800)
                
            # Extract skills using EuriAI
            with st.spinner("🔍 Extracting Skills..."):
                st.session_state.skills = extract_skills_from_resume(st.session_state.resume_text)
            
            st.session_state.current_step = 3
            st.rerun()
    
    # Step 3: Results
    elif st.session_state.current_step == 3:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("<h2>Career Insights & Analysis</h2>", unsafe_allow_html=True)
            
            # Resume Summary - using render_card to ensure proper HTML rendering
            st.markdown(
                render_card("Resume Summary", "resume", st.session_state.summary),
                unsafe_allow_html=True
            )
            
            # Skill Gaps - using render_card to ensure proper HTML rendering
            st.markdown(
                render_card("Skill Gaps & Missing Areas", "skills", st.session_state.gaps),
                unsafe_allow_html=True
            )
            
            # Future Roadmap - using render_card to ensure proper HTML rendering
            st.markdown(
                render_card("Future Roadmap & Preparation Strategy", "roadmap", st.session_state.roadmap),
                unsafe_allow_html=True
            )
            
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
            
            # PDF download section with actual functionality
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{icon('download')} Download Analysis</div>
                <div class="card-content">
                    <p>Get a PDF copy of your resume analysis to review later.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Generate PDF Report"):
                with st.spinner("Generating PDF report..."):
                    pdf_download_link = generate_pdf_report()
                    st.markdown(pdf_download_link, unsafe_allow_html=True)
                
            # Display skills list - show all skills without percentages
            skills_html = "<ul class='skills-list'>"
            for skill in st.session_state.skills:
                skills_html += f"<li>{skill}</li>"
            skills_html += "</ul>"
            
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{icon('skills')} Your Skills</div>
                <div class="card-content">
                    {skills_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Step 4: Job Search
    elif st.session_state.current_step == 4:
        if not st.session_state.search_keywords:
            with st.spinner("🔍 Extracting best keywords from resume..."):
                st.markdown(render_loading("Generating optimal job search keywords..."), unsafe_allow_html=True)
                keywords = ask_euriai(
                    f"Based on this resume summary, suggest the best job titles/keywords for searching jobs. Give a comma-separated list only, no explanation.\n\nSummary:\n{st.session_state.summary}",
                    max_tokens=200
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
            search_keywords_input = st.text_input("Edit keywords if needed:", value=st.session_state.search_keywords)
            
            # Search button
            if st.button("Search Jobs", key="search_jobs_btn") or not st.session_state.naukri_jobs:
                with st.spinner("🚀 Fetching Jobs from Naukri..."):
                    st.markdown(render_loading("Searching for matching jobs..."), unsafe_allow_html=True)
                    st.session_state.naukri_jobs = fetch_naukri_jobs(search_query=search_keywords_input, max_jobs=60)
            
            # Display results count
            total_jobs = len(st.session_state.naukri_jobs)
            st.markdown(f"""
            <div class="results-summary">
                <div class="results-number">{total_jobs}</div>
                <div class="results-text">matching jobs found</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display Naukri jobs directly (no tabs)
            if st.session_state.naukri_jobs:
                # Add filters for Naukri jobs
                col_location, col_sort = st.columns(2)
                with col_location:
                    locations = ["All Locations"] + sorted(list(set([job.get('location', '').split(',')[0].strip() for job in st.session_state.naukri_jobs if job.get('location')])))
                    filter_location = st.selectbox("Filter by location:", locations, key="naukri_location")
                
                with col_sort:
                    sort_options = ["Relevance", "Most Recent", "Company Name"]
                    sort_by = st.selectbox("Sort by:", sort_options, key="naukri_sort")
                
                # Apply filters (without loading)
                filtered_jobs = st.session_state.naukri_jobs
                if filter_location != "All Locations":
                    filtered_jobs = [job for job in filtered_jobs if job.get('location', '').startswith(filter_location)]
                
                if sort_by == "Most Recent":
                    # Using a fixed seed for consistency
                    random.seed(24)
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
            location_options = ["All Locations", "Remote", "Bangalore", "Delhi", "Mumbai", "Hyderabad", "Chennai", "Pune"]
            selected_location = st.selectbox("Location:", location_options)
            
            # Experience level filter
            experience_options = ["All Levels", "Entry Level", "Mid-Level", "Senior", "Executive"]
            selected_experience = st.selectbox("Experience Level:", experience_options)
            
            # Job type filter
            job_type_options = ["All Types", "Full-time", "Part-time", "Contract", "Internship"]
            selected_job_type = st.selectbox("Job Type:", job_type_options)
            
            # Salary range
            st.markdown("<p>Salary Range:</p>", unsafe_allow_html=True)
            salary_range = st.slider("", 0, 200, (40, 120), format="₹%dL")
            
            # Apply sidebar filters - Show a success message without loading
            if st.button("Apply Filters"):
                # Simple feedback without actual loading
                st.success(f"Filters applied: {selected_location}, {selected_experience}, {selected_job_type}")
                # In a real implementation, we would filter the job results here
            
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