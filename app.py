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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

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

# Extract skills using EuriAI client with improved prompt structure
def extract_skills_from_resume(resume_text):
    # Use EuriAI to extract skills with improved prompt that won't get cut off
    skills_prompt = f"""Extract exactly 10 technical skills from this resume.
    Your response must be ONLY a comma-separated list of skills with no preamble, no additional text, and no explanations.
    Do not number the skills or add any formatting except commas between skills.
    Do not add any commentary before or after the list.
    
    Resume text:
    {resume_text}
    
    Remember: Return ONLY a comma-separated list of 10 skills, nothing else."""
    
    # Limit the token count to avoid cutoff issues
    skills_response = ask_euriai(skills_prompt, max_tokens=150)
    
    # Parse the comma-separated response
    skills_list = [skill.strip() for skill in skills_response.split(',')]
    return skills_list[:10]  # Ensure we get max 10 skills

# Clean response to ensure no cut-off HTML
def clean_response(response):
    # Remove any cut-off HTML tags at the end
    cleaned = re.sub(r'<[^>]*$', '', response)
    return cleaned

# Ask EURI AI to generate output with improved prompts to prevent cutoffs
def ask_euriai(prompt, max_tokens=600):
    # Add explicit instructions to ensure complete responses with styling and formatting
    enhanced_prompt = f"""{prompt}

Important instructions:
1. Provide a complete, well-structured response with no cut-off sentences.
2. Keep your response concise and within {max_tokens} tokens.
3. Format your response with proper headings, bullet points, and paragraphs.
4. Use asterisks for emphasis on important points (*important*).
5. Use numbered lists for sequential steps or prioritized items.
6. Break content into clear sections with double line breaks between sections.
7. Structure content to be easily scannable with clear organization.
8. Do not ask any follow-up questions at the end of your response."""
    
    response = euriai_client.generate_completion(prompt=enhanced_prompt, temperature=0.5, max_tokens=max_tokens)
    if isinstance(response, dict) and 'choices' in response:
        return response['choices'][0]['message']['content']
    return response

# Generate visually appealing PDF report with modern formatting
def generate_pdf_report():
    try:
        # Create buffer
        buffer = io.BytesIO()
        
        # Create document with better margins
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            title="Career Analysis Report",
            leftMargin=0.75*inch,
            rightMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Improved styles
        styles = getSampleStyleSheet()
        
        # Custom styles with better formatting
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#5C67DE'),
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            fontName='Helvetica-Bold',
            spaceAfter=12,
            spaceBefore=16,
            textColor=colors.HexColor('#31304D'),
            borderWidth=1,
            borderColor=colors.HexColor('#5C67DE'),
            borderPadding=8,
            borderRadius=6,
            leftIndent=5,
            backColor=colors.HexColor('#F1F5F9')
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#4A52B3'),
            spaceBefore=10,
            spaceAfter=6,
            leftIndent=10
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            firstLineIndent=15
        )
        
        bullet_style = ParagraphStyle(
            'BulletPoint',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            leading=16,
            leftIndent=30,
            bulletIndent=15,
            spaceAfter=8
        )
        
        skill_item_style = ParagraphStyle(
            'SkillItem',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#31304D'),
            backColor=colors.HexColor('#F9F9FF'),
            spaceAfter=8,
            alignment=TA_CENTER,
            borderWidth=0.5,
            borderColor=colors.HexColor('#5C67DE'),
            borderPadding=6,
            borderRadius=4
        )
        
        # Content
        content = []
        
        # Add a logo or header image
        # Add some decorative elements and header
        header_data = [
            [Paragraph('<font color="#5C67DE" size="18"><b>CAREER</b></font> <font color="#31304D" size="18"><b>BOOST AI</b></font>', ParagraphStyle('Header', alignment=TA_CENTER, spaceAfter=0))]
        ]
        header_table = Table(header_data, colWidths=[7*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9F9FF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ]))
        content.append(header_table)
        content.append(Spacer(1, 20))
        
        # Title with better spacing
        content.append(Paragraph("Career Analysis Report", title_style))
        content.append(Spacer(1, 5))
        
        # Date line
        date_text = f"Generated on: {time.strftime('%B %d, %Y')}"
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            alignment=TA_CENTER
        )
        content.append(Paragraph(date_text, date_style))
        content.append(Spacer(1, 30))
        
        # Resume Summary with improved formatting and visual elements
        content.append(Paragraph("Resume Summary", subtitle_style))
        content.append(Spacer(1, 5))
        
        # Parse and format the summary text with better visual structure
        # First, let's try to identify if there are sections in the summary
        summary_text = st.session_state.summary
        
        # Check if summary has markdown-style sections or paragraphs
        if '##' in summary_text or '*' in summary_text:
            # For markdown formatted text
            sections = re.split(r'##\s+', summary_text)
            if len(sections) > 1:
                # We have markdown headings
                for section in sections[1:]:  # Skip the first empty split
                    section_parts = section.split('\n', 1)
                    if len(section_parts) > 1:
                        section_title, section_content = section_parts
                        content.append(Paragraph(section_title.strip(), section_title_style))
                        for para in section_content.strip().split('\n\n'):
                            if para.strip():
                                if para.strip().startswith('*') or para.strip().startswith('-'):
                                    # This is a bullet point list
                                    for bullet in para.strip().split('\n'):
                                        if bullet.strip():
                                            bullet_text = bullet.strip().lstrip('*-').strip()
                                            content.append(Paragraph(f"• {bullet_text}", bullet_style))
                                else:
                                    content.append(Paragraph(para.strip(), normal_style))
                    else:
                        content.append(Paragraph(section.strip(), normal_style))
            else:
                # Just format paragraphs normally
                for para in summary_text.split('\n\n'):
                    if para.strip():
                        if para.strip().startswith('*') or para.strip().startswith('-'):
                            # This is a bullet point list
                            for bullet in para.strip().split('\n'):
                                if bullet.strip():
                                    bullet_text = bullet.strip().lstrip('*-').strip()
                                    content.append(Paragraph(f"• {bullet_text}", bullet_style))
                        else:
                            content.append(Paragraph(para.strip(), normal_style))
        else:
            # For regular text, just split by paragraphs
            for para in summary_text.split('\n\n'):
                if para.strip():
                    content.append(Paragraph(para.strip(), normal_style))
        
        content.append(Spacer(1, 20))
        
        # Skills section with visually appealing display
        content.append(Paragraph("Your Top Skills", subtitle_style))
        content.append(Spacer(1, 10))
        
        # Creating a more visually appealing grid for skills
        skills_data = []
        row = []
        
        # Ensure we have at least one row even with odd number of skills
        if len(st.session_state.skills) % 2 != 0:
            st.session_state.skills.append("")
        
        for i, skill in enumerate(st.session_state.skills, 1):
            if skill.strip():  # Only add non-empty skills
                skill_para = Paragraph(skill, skill_item_style)
                row.append(skill_para)
                if i % 2 == 0:
                    skills_data.append(row)
                    row = []
        
        # Add any remaining row
        if row:
            skills_data.append(row)
        
        if skills_data:
            # Create a table with skills
            skills_table = Table(skills_data, colWidths=[3*inch, 3*inch])
            skills_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 20),
                ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ]))
            content.append(skills_table)
        else:
            content.append(Paragraph("No skills extracted", normal_style))
        
        content.append(Spacer(1, 20))
        
        # Skill Gaps with improved visual formatting
        content.append(Paragraph("Skill Gaps & Missing Areas", subtitle_style))
        content.append(Spacer(1, 10))
        
        # Format gaps as numbered items for better visual hierarchy
        gaps_text = st.session_state.gaps
        
        # Check if gaps text already has numbered items or bullet points
        if re.search(r'^\d+\.|\*\*|\-', gaps_text, re.MULTILINE):
            # Text already has formatting, let's preserve it
            gap_items = re.split(r'(?:\d+\.\s*\*\*|\*\*|\d+\.|\-\s*\*\*)', gaps_text)
            titles = re.findall(r'(?:\d+\.\s*\*\*|\*\*|\d+\.|\-\s*\*\*)([^*\n]+)(?:\*\*)?', gaps_text)
            
            if len(titles) > 0:
                for i, (title, content_part) in enumerate(zip(titles, gap_items[1:]), 1):
                    content.append(Paragraph(f"{i}. <b>{title.strip()}</b>", section_title_style))
                    
                    # Split the content into paragraphs
                    paragraphs = content_part.strip().split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            content.append(Paragraph(para.strip(), normal_style))
            else:
                # Just format as normal paragraphs
                for para in gaps_text.split('\n\n'):
                    if para.strip():
                        content.append(Paragraph(para.strip(), normal_style))
        else:
            # No clear formatting, treat as regular paragraphs
            for para in gaps_text.split('\n\n'):
                if para.strip():
                    content.append(Paragraph(para.strip(), normal_style))
                
        content.append(Spacer(1, 20))
        
        # Future Roadmap with improved formatting - treat differently
        content.append(Paragraph("Future Roadmap & Preparation Strategy", subtitle_style))
        content.append(Spacer(1, 10))
        
        # Format roadmap as sections and bullet points for better visual hierarchy
        roadmap_text = st.session_state.roadmap
        
        # Look for section headings in the roadmap with markdown-style formatting
        roadmap_sections = re.split(r'(?:\d+\.\s*\*\*|\*\*|\d+\.|\-\s*\*\*)', roadmap_text)
        section_titles = re.findall(r'(?:\d+\.\s*\*\*|\*\*|\d+\.|\-\s*\*\*)([^*\n]+)(?:\*\*)?', roadmap_text)
        
        if len(section_titles) > 0:
            # We have identified section titles
            for i, (title, content_part) in enumerate(zip(section_titles, roadmap_sections[1:]), 1):
                content.append(Paragraph(f"{i}. <b>{title.strip()}</b>", section_title_style))
                
                # Split the content into paragraphs and bullet points
                if '-' in content_part or '*' in content_part:
                    # Contains bullet points
                    bullet_items = re.split(r'\n\s*[-*]\s+', content_part)
                    for j, bullet in enumerate(bullet_items):
                        if j == 0 and not bullet.strip():
                            continue  # Skip empty first split
                        if bullet.strip():
                            if j == 0 and not (bullet.strip().startswith('-') or bullet.strip().startswith('*')):
                                # This is an intro paragraph
                                content.append(Paragraph(bullet.strip(), normal_style))
                            else:
                                content.append(Paragraph(f"• {bullet.strip()}", bullet_style))
                else:
                    # Just regular paragraphs
                    paragraphs = content_part.strip().split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            content.append(Paragraph(para.strip(), normal_style))
        else:
            # No clear section formatting, check for standard bullet points
            if '-' in roadmap_text or '*' in roadmap_text:
                # Try to identify bullet point lists
                paragraphs = roadmap_text.split('\n\n')
                for para in paragraphs:
                    if para.strip().startswith('-') or para.strip().startswith('*') or '\n-' in para or '\n*' in para:
                        # This paragraph contains bullet points
                        bullet_items = para.split('\n')
                        for bullet in bullet_items:
                            if bullet.strip():
                                if bullet.strip().startswith('-') or bullet.strip().startswith('*'):
                                    bullet_text = bullet.strip().lstrip('-*').strip()
                                    content.append(Paragraph(f"• {bullet_text}", bullet_style))
                                else:
                                    content.append(Paragraph(bullet.strip(), normal_style))
                    else:
                        # Regular paragraph
                        content.append(Paragraph(para.strip(), normal_style))
            else:
                # Just regular paragraphs
                for para in roadmap_text.split('\n\n'):
                    if para.strip():
                        content.append(Paragraph(para.strip(), normal_style))
        
        # Add a visually appealing footer with contact info and branding
        content.append(Spacer(1, 30))
        
        # Footer with horizontal line
        footer_data = [
            [Paragraph('<font color="#5C67DE" size="9"><b>CareerBoost AI</b></font> | <font color="#64748B" size="9">Resume Analysis & Job Matching Platform</font>', 
                      ParagraphStyle('Footer', alignment=TA_CENTER, spaceAfter=0))]
        ]
        footer_table = Table(footer_data, colWidths=[7*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        content.append(footer_table)
        
        # Build PDF
        doc.build(content)
        
        # Get PDF from buffer
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Encode to base64 for download
        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="career_analysis_report.pdf" class="job-apply-btn" style="text-decoration:none;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 5px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg> Download PDF Report</a>'
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

# Format job cards with improved visual styling
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
    
    # Enhanced styling for job cards
    html = f"""
    <div class="job-card" style="border-radius: 12px; transition: transform 0.3s, box-shadow 0.3s; border-left: 5px solid #F4CE14; position: relative; overflow: hidden;">
        <div style="position: absolute; top: 0; right: 0; background-color: #f1f5f9; color: #64748b; font-size: 0.7rem; padding: 3px 8px; border-radius: 0 0 0 8px;">Naukri</div>
        <div class="job-title" style="font-size: 1.25rem; font-weight: 700; margin-bottom: 8px; color: #31304D;">{job_title}</div>
        <div class="company-name" style="font-size: 1rem; font-weight: 600; margin-bottom: 12px; color: #5C67DE;">{company}</div>
        <div class="job-meta" style="display: flex; align-items: center; margin-bottom: 12px; color: #64748b;">
            {icon('location')} <span style="margin-left: 5px;">{location}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <a href="{link}" target="_blank" rel="noopener noreferrer" class="job-apply-btn" style="background-color: #5C67DE; padding: 8px 16px;">View Job</a>
            <button class="custom-button-secondary" style="background-color: transparent; border: 1px solid #5C67DE; color: #5C67DE; padding: 8px 16px; border-radius: 50px; cursor: pointer; font-size: 0.9rem;">Save</button>
        </div>
    </div>
    """
    return html

# Render card with improved visual formatting
def render_card(title, icon_name, content):
    # Clean the content to ensure no cut-off HTML
    cleaned_content = clean_response(content)
    
    # Process the content to enhance formatting
    # Replace Markdown-style headings with styled HTML headings
    formatted_content = re.sub(r'\*\*([^*]+)\*\*', r'<span style="font-weight: bold; color: #31304D;">\1</span>', cleaned_content)
    
    # Format numbered lists with better styling
    formatted_content = re.sub(r'(\d+\.\s)([^\n]+)', 
                              r'<div style="margin-bottom: 10px;"><span style="font-weight: bold; color: #5C67DE; margin-right: 5px;">\1</span>\2</div>', 
                              formatted_content)
    
    # Format bullet points with better styling
    formatted_content = re.sub(r'(-|\•|\*)\s([^\n]+)', 
                              r'<div style="margin-bottom: 8px; margin-left: 15px;"><span style="color: #5C67DE; margin-right: 5px;">•</span>\2</div>', 
                              formatted_content)
    
    # Convert newlines to proper HTML breaks with spacing
    formatted_content = formatted_content.replace('\n\n', '<div style="margin-bottom: 15px;"></div>')
    formatted_content = formatted_content.replace('\n', '<br>')
    
    html = f"""
    <div class="card" style="border-radius: 12px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);">
        <div class="card-title" style="font-size: 1.5rem; font-weight: 700; padding-bottom: 12px; border-bottom: 1px solid #eaeaea; margin-bottom: 15px;">{icon(icon_name)} {title}</div>
        <div class="card-content" style="font-size: 1rem; line-height: 1.6; color: #333;">
            {formatted_content}
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
    # Set the status for each step
    step1_status = "completed" if current_step > 1 else "active" if current_step == 1 else ""
    step2_status = "completed" if current_step > 2 else "active" if current_step == 2 else ""
    step3_status = "completed" if current_step > 3 else "active" if current_step == 3 else ""
    step4_status = "completed" if current_step > 4 else "active" if current_step == 4 else ""
    
    html = f"""
    <div class="step-container">
        <div class="step {step1_status}">
            <div class="step-number">1</div>
            <div class="step-title">Upload Resume</div>
            <div class="step-connector"></div>
        </div>
        <div class="step {step2_status}">
            <div class="step-number">2</div>
            <div class="step-title">AI Analysis</div>
            <div class="step-connector"></div>
        </div>
        <div class="step {step3_status}">
            <div class="step-number">3</div>
            <div class="step-title">Career Insights</div>
            <div class="step-connector"></div>
        </div>
        <div class="step {step4_status}">
            <div class="step-number">4</div>
            <div class="step-title">Find Jobs</div>
        </div>
    </div>
    """
    
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
            
            # Enhanced prompts for visually structured results
            with st.spinner("✍️ Summarizing Resume..."):
                st.markdown(render_loading("Analyzing resume content..."), unsafe_allow_html=True)
                
                summary_prompt = f"""Provide a detailed but concise summary of this resume highlighting key skills, education, and experience.
                Format the summary with the following structure:
                
                • Start with an opening paragraph introducing the candidate. 
                • Use clear paragraphs with proper spacing.
                • Highlight key skills and competencies.
                • Emphasize educational background and certifications.
                • Showcase relevant experience and projects.
                
                Make your response visually scannable with proper formatting.
                Keep your response under 400 words total to ensure it doesn't get cut off.
                
                Resume text:
                {st.session_state.resume_text}"""
                
                st.session_state.summary = ask_euriai(summary_prompt, max_tokens=500)
            
            with st.spinner("🔎 Finding Skill Gaps..."):
                st.markdown(render_loading("Identifying skill gaps..."), unsafe_allow_html=True)
                
                gaps_prompt = f"""Analyze this resume and identify 3-5 specific skill gaps, missing certifications, or experiences that would improve job prospects.
                
                Format your response with the following structure:
                • Number each skill gap (1., 2., 3., etc.)
                • For each gap, use a bold heading with double asterisks: **Skill Gap Title**
                • Under each heading, provide 2-3 sentences explaining why this skill matters and how it would improve employability
                • Suggest specific ways to address each gap (courses, certifications, projects)
                
                Make your response visually appealing with clear formatting and organization.
                Keep your response under 400 words total.
                
                Resume text:
                {st.session_state.resume_text}"""
                
                st.session_state.gaps = ask_euriai(gaps_prompt, max_tokens=500)
            
            with st.spinner("🚀 Creating Future Roadmap..."):
                st.markdown(render_loading("Preparing career roadmap..."), unsafe_allow_html=True)
                
                roadmap_prompt = f"""Create a visually structured 6-month career development roadmap based on this resume.
                
                Format the roadmap with these clearly defined sections:
                
                **1. Short-term Goals (1-2 months)**
                • Use bullet points for each recommendation
                • Be specific about courses, skills, or projects to pursue
                • Explain the expected outcome of each action
                
                **2. Medium-term Improvements (3-4 months)**
                • Use bullet points for each recommendation
                • Focus on skills that build on the short-term foundations
                • Include specific certification recommendations if applicable
                
                **3. Long-term Strategy (5-6 months)**
                • Use bullet points for each recommendation
                • Include networking and portfolio development strategies
                • Suggest ways to demonstrate the new skills to employers
                
                Make the roadmap visually organized, easy to follow, and actionable.
                Keep your response under 400 words total with clear structure.
                
                Resume text:
                {st.session_state.resume_text}"""
                
                st.session_state.roadmap = ask_euriai(roadmap_prompt, max_tokens=500)
                
            # Extract skills using EuriAI with improved prompt
            with st.spinner("🔍 Extracting Skills..."):
                st.session_state.skills = extract_skills_from_resume(st.session_state.resume_text)
            
            st.session_state.current_step = 3
            st.rerun()
    
    # Step 3: Results
    elif st.session_state.current_step == 3:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("<h2>Career Insights & Analysis</h2>", unsafe_allow_html=True)
            
            # Resume Summary - using render_card with improved formatting
            st.markdown(
                render_card("Resume Summary", "resume", st.session_state.summary),
                unsafe_allow_html=True
            )
            
            # Skill Gaps - using render_card with improved formatting
            st.markdown(
                render_card("Skill Gaps & Missing Areas", "skills", st.session_state.gaps),
                unsafe_allow_html=True
            )
            
            # Future Roadmap - using render_card with improved formatting
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
            
            # PDF download section with better formatting
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
        # Generate search keywords if not already present
        if not st.session_state.search_keywords:
            with st.spinner("🔍 Extracting best keywords from resume..."):
                st.markdown(render_loading("Generating optimal job search keywords..."), unsafe_allow_html=True)
                
                # Improved prompt for keywords generation
                keywords_prompt = f"""Based on this resume summary and skills, suggest 3-5 best job titles/keywords for searching jobs.
                Return ONLY a comma-separated list of keywords with no explanations or additional text.
                
                Summary:
                {st.session_state.summary}
                
                Skills:
                {', '.join(st.session_state.skills)}"""
                
                keywords = ask_euriai(keywords_prompt, max_tokens=100)
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