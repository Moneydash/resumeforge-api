from flask import Blueprint, request, jsonify, render_template, send_file, current_app
from weasyprint import HTML, CSS
import os
import json
import tempfile
import uuid
from datetime import datetime
import logging
from utils.helper import calcHeightModern1, format_date, format_description, export_pdf_response

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_pdf():
    """Generate a PDF resume from the provided data and return it as a preview"""
    try:
        # Get resume data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No resume data provided'}), 400
            
        # Create a temporary directory to store the generated PDF
        temp_dir = tempfile.gettempdir()
        filename = f"resume_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(temp_dir, filename)
        
        # Generate HTML content from resume data
        html_content = generate_resume_html(data)
        dynamic_height = calcHeightModern1(data)
        # Generate PDF using WeasyPrint
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string=get_default_css(dynamic_height))]
        )
        
        # Return the generated PDF file as a preview (not as an attachment)
        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"resume_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def export_pdf():
    """Generate a PDF resume from the provided data and export it as a PDF File"""
    try:
        # Get resume data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No resume data provided'}), 400
        html_content = generate_resume_html(data)
        dynamic_height = calcHeightModern1(data)
        css_content = get_default_css(dynamic_height)
        return export_pdf_response(html_content, css_content)
    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def generate_resume_html(resume_data):
    """Generate HTML content from resume data based on Modern template"""
    # Modern template for a resume with two-column layout
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{resume_data.get('personal', {}).get('name', 'Resume')}</title>
    </head>
    <body>
        <div class="resume-container">
            <!-- Header / Personal Info with blue gradient background -->
            <header class="header">
                <h1 class="name">{resume_data.get('personal', {}).get('name', '')}</h1>
                <h2 class="headline">{resume_data.get('personal', {}).get('headline', '')}</h2>
                <div class="contact-info">
                    {f'<p class="email">{resume_data.get("personal", {}).get("email", "")}</p>' if resume_data.get('personal', {}).get('email') else ''}
                    {f'<p class="location">{resume_data.get("personal", {}).get("location", "")}</p>' if resume_data.get('personal', {}).get('location') else ''}
                    {f'<p class="website"><a href="{resume_data.get("personal", {}).get("website", {}).get("link", "")}">{resume_data.get("personal", {}).get("website", {}).get("name", "") or resume_data.get("personal", {}).get("website", {}).get("link", "")}</a></p>' if resume_data.get('personal', {}).get('website', {}).get('link') else ''}
                </div>
                
                <!-- Social Links -->
                <div class="social-links">
                    {f'<a href="https://linkedin.com/in/{resume_data.get("socials", {}).get("linkedIn", "").strip("https://linkedin.com/in/")}">LinkedIn</a>' if resume_data.get('socials', {}).get('linkedIn') else ''}
                    {f'<a href="https://github.com/{resume_data.get("socials", {}).get("github", "").strip("https://github.com/")}">GitHub</a>' if resume_data.get('socials', {}).get('github') else ''}
                    {f'<a href="https://twitter.com/{resume_data.get("socials", {}).get("twitter", "").strip("https://twitter.com/")}">Twitter</a>' if resume_data.get('socials', {}).get('twitter') else ''}
                </div>
            </header>
            
            <!-- Main Content with two-column layout -->
            <div class="main-content">
                <!-- Left Column: Summary, Experience, Education, Projects -->
                <div class="left-column">
                    <!-- Summary -->
                    {f'<section class="section"><h2 class="section-title">About Me</h2><div class="summary"><p>{format_description(resume_data.get("summary", ""))}</p></div></section>' if resume_data.get('summary') else ''}
                    
                    <!-- Work Experience -->
                    {f'<section class="section"><h2 class="section-title">Work Experience</h2><div class="section-content">' if resume_data.get('experience') else ''}
    '''
    
    # Add work experience
    for job in resume_data.get('experience', []):
        html += f'''
                    <div class="item">
                        <div class="item-header">
                            <h3 class="item-title">{job.get('title', '')}</h3>
                            <p class="item-subtitle">{job.get('company', '')}</p>
                            <div class="item-date">{format_date(job.get('startDate', ''))} - {format_date(job.get('endDate', '')) if job.get('endDate') else 'Present'}</div>
                        </div>
                        <div class="item-description">
                            <p>{format_description(job.get('description', ''))}</p>
                        </div>
                    </div>
        '''
    
    # Close experience section if it exists
    if resume_data.get('experience'):
        html += '''
                    </div>
                </section>
        '''
    
    # Education
    if resume_data.get('education'):
        html += '''
                <section class="section">
                    <h2 class="section-title">Education</h2>
                    <div class="section-content">
        '''
        
        for edu in resume_data.get('education', []):
            html += f'''
                        <div class="item">
                            <div class="item-header">
                                <h3 class="item-title">{edu.get('degree', '')}</h3>
                                <p class="item-subtitle">{edu.get('institution', '')}</p>
                                <div class="item-date">{format_date(edu.get('startDate', ''))} - {format_date(edu.get('endDate')) if edu.get('endDate') else 'Present'}</div>
                            </div>
                        </div>
            '''
            
        html += '''
                    </div>
                </section>
        '''
    
    # Close left column
    html += '''
                </div>
                
                <!-- Right Column: Skills, Languages, Certifications, Awards, Interests, References -->
                <div class="right-column">
    '''
    
    # Skills
    if resume_data.get('skills', {}).get('programmingLanguages') or resume_data.get('skills', {}).get('keywords'):
        html += '''
                    <section class="section">
                        <h2 class="section-title">Skills</h2>
                        <div class="section-content">
        '''
        
        # Programming languages
        if resume_data.get('skills', {}).get('programmingLanguages'):
            html += '''
                            <div class="skill-group">
                                <h3 class="skill-group-title">Programming Languages</h3>
                                <div class="skill-keywords">
            '''
            
            for lang in resume_data.get('skills', {}).get('programmingLanguages', []):
                html += f'''
                                    <span class="keyword">{lang}</span>
                '''
                
            html += '''
                                </div>
                            </div>
            '''
        
        # Other skills/keywords
        if resume_data.get('skills', {}).get('keywords'):
            html += '''
                            <div class="skill-group">
                                <h3 class="skill-group-title">Technologies & Tools</h3>
                                <div class="skill-keywords">
            '''
            
            for keyword in resume_data.get('skills', {}).get('keywords', []):
                html += f'''
                                    <span class="keyword">{keyword}</span>
                '''
                
            html += '''
                                </div>
                            </div>
            '''
            
        html += '''
                        </div>
                    </section>
        '''

    # Projects
    if resume_data.get('projects'):
        html += '''
                <section class="section">
                    <h2 class="section-title">Projects</h2>
                    <div class="section-content">
        '''
        
        for project in resume_data.get('projects', []):
            html += f'''
                        <div class="item">
                            <div class="item-header">
                                <h3 class="item-title">{project.get('title', '')}</h3>
                            </div>
                            <div class="item-description">
                                <p>{format_description(project.get('description', ''))}</p>
                            </div>
                            {f'<div class="project-technologies">' if project.get('technologies') else ''}
            '''
            
            for tech in project.get('technologies', []):
                html += f'''
                                <span class="technology">{tech}</span>
                '''
                
            if project.get('technologies'):
                html += '''
                            </div>
                '''
                
            html += '''
                        </div>
            '''
            
        html += '''
                    </div>
                </section>
        '''
    
    # Languages
    if resume_data.get('languages'):
        html += '''
                    <section class="section">
                        <h2 class="section-title">Languages</h2>
                        <div class="section-content">
                            <div class="languages">
        '''
        
        for language in resume_data.get('languages', []):
            html += f'''
                                <span class="language">{language}</span>
            '''
            
        html += '''
                            </div>
                        </div>
                    </section>
        '''
    
    # Certifications
    if resume_data.get('certifications'):
        html += '''
                    <section class="section">
                        <h2 class="section-title">Certifications</h2>
                        <div class="section-content">
        '''
        
        for cert in resume_data.get('certifications', []):
            html += f'''
                            <div class="item">
                                <div class="item-header">
                                    <h3 class="item-title">{cert.get('name', '')}</h3>
                                    <p class="item-subtitle">{cert.get('issuingOrganization', '')}</p>
                                    <div class="item-date">{format_date(cert.get('date', ''))}</div>
                                </div>
                            </div>
            '''
            
        html += '''
                        </div>
                    </section>
        '''
    
    # Awards
    if resume_data.get('awards'):
        html += '''
                    <section class="section">
                        <h2 class="section-title">Awards</h2>
                        <div class="section-content">
        '''
        
        for award in resume_data.get('awards', []):
            html += f'''
                            <div class="item">
                                <div class="item-header">
                                    <h3 class="item-title">{award.get('title', '')}</h3>
                                    <div class="item-date">{award.get('date', '')}</div>
                                </div>
                                {f'<div class="item-description"><p>{award.get("description", "")}</p></div>' if award.get('description') else ''}
                            </div>
            '''
            
        html += '''
                        </div>
                    </section>
        '''
    
    # Interests
    if resume_data.get('interests'):
        html += '''
                    <section class="section">
                        <h2 class="section-title">Interests</h2>
                        <div class="section-content">
                            <div class="interests">
        '''
        
        for interest in resume_data.get('interests', []):
            html += f'''
                                <span class="interest">{interest}</span>
            '''
            
        html += '''
                            </div>
                        </div>
                    </section>
        '''
    
    # References
    if resume_data.get('references'):
        html += '''
                    <section class="section">
                        <h2 class="section-title">References</h2>
                        <div class="section-content">
        '''
        
        for ref in resume_data.get('references', []):
            html += f'''
                            <div class="reference">
                                <h3 class="item-title">{ref.get('name', '')}</h3>
                                <p class="item-subtitle">{ref.get('title', '')} at {ref.get('company', '')}</p>
                                <div class="reference-contact">
                                    <p>Email: {ref.get('email', '')}</p>
                                    <p>Phone: {ref.get('phone', '')}</p>
                                </div>
                            </div>
            '''
            
        html += '''
                        </div>
                    </section>
        '''
    
    # Close right column and main content
    html += '''
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

    return html


def get_default_css(dynamic_height):
    """Return default CSS for the resume based on Modern template"""
    dynamic_height -= 550 # remove some of the height
    css = f"""
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@300;400;500;600;700&display=swap');

    @page {{
        margin: 0;
        size: 612pt {dynamic_height}pt;
    }}
    """

    css += '''
    * {
        box-sizing: border-box;
    }

    body {
        font-family: 'IBM Plex Serif', serif;
        color: #333;
        background-color: #fff;
    }

    .resume-container {
        max-width: 8.5in;
        background-color: #fff;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    }

    /* Header Styles */
    .header {
        background: linear-gradient(90deg,rgba(73, 64, 245, 1) 0%, rgba(67, 67, 222, 1) 21%, rgba(0, 212, 255, 1) 100%);
        color: white;
        padding-top: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 2rem;
        margin-bottom: 0;
    }

    .name {
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .headline {
        font-size: 1.35rem;
        font-weight: 400;
        margin-top: -1rem;
        margin-left: 0.25rem;
        opacity: 0.9;
    }

    .contact-info {
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        margin-bottom: 1rem;
        margin-left: 0.25rem;
        font-size: 0.95rem;
    }

    .contact-info p {
        margin: 0;
    }

    .contact-info a {
        color: white;
        text-decoration: none;
    }

    .social-links {
        display: flex;
        gap: 1rem;
        margin-bottom: 0.35rem;
    }

    .social-links a {
        color: white;
        text-decoration: none;
        background-color: rgba(255, 255, 255, 0.2);
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
        transition: background-color 0.2s;
    }

    .social-links a:hover {
        background-color: rgba(255, 255, 255, 0.3);
    }

    /* Main Content Layout */
    .main-content {
        display: flex;
        padding: 0.5rem;
    }

    .left-column {
        flex: 2;
        padding-right: 2rem;
    }

    .right-column {
        flex: 1.5;
        padding-left: 1rem;
    }

    /* Summary Styles */
    .summary {
        line-height: 1.5;
        font-size: 1.05rem;
        color: #4b5563;
    }

    /* Section Styles */
    .section {
        margin-bottom: 2rem;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 600;
        color: #2563eb;
        padding-bottom: 0.35rem;
        border-bottom: 2px solid #e5e7eb;
    }

    .section-content {
        padding-top: -1.25rem;
    }

    /* Item Styles (for experience, education, etc.) */
    .item {
        margin-bottom: 1.5rem;
    }

    .item-header {
        margin-bottom: 0.75rem;
    }

    .item-title {
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: -0.75rem;
        color: #1f2937;
    }

    .item-subtitle {
        font-size: 1rem;
        color: #4b5563;
        margin-bottom: 0.25rem;
        font-weight: 500;
    }

    .item-date {
        font-size: 0.9rem;
        color: #6b7280;
        font-style: italic;
    }

    .item-description {
        font-size: 0.95rem;
        color: #4b5563;
        line-height: 1.6;
    }

    /* Skills Styles */
    .skill-group {
        margin-bottom: 1.25rem;
    }

    .skill-group-title {
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        color: #4b5563;
    }

    .skill-keywords, .languages, .interests {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }

    .keyword, .language, .interest {
        background-color: #0496C7;
        color: #FFF;
        padding: 0.25rem 0.75rem;
        border-radius: 50px;
        font-size: 0.85rem;
        display: inline-block;
    }

    .technology {
        background-color: #dbeafe;
        color: #2563eb;
        padding: 0.25rem 0.75rem;
        border-radius: 50px;
        font-size: 0.85rem;
        display: inline-block;
    }

    /* Project Styles */
    .project-technologies {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.75rem;
    }

    /* Reference Styles */
    .reference {
        background-color: #f3f4f6;
        padding: 1.25rem;
        border-radius: 6px;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }

    .reference-contact {
        margin-top: 0.75rem;
        font-size: 0.9rem;
        color: #4b5563;
    }
    
    .reference-contact p {
        margin: 2px 0;
    }
    '''
    return css
