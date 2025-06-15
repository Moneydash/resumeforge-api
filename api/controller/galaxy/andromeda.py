import os
from flask import request, jsonify, current_app, redirect
import logging
from utils.helper import css_height_calc, data_caching, format_date, format_description, upload_pdf_to_supabase
import json
import hashlib

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

max_attempts = 50 # maximum attempts in loop
supabase_bucket_name = os.getenv("SUPABASE_BUCKET_NAME", "bucket_name")

def generate_pdf():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No resume data provided'}), 400

        name = data.get('personal', {}).get('name')
        cached_pdf = data_caching(data, "andromeda")
        if cached_pdf:
            # If we have a cached URL, redirect to it
            if cached_pdf.startswith("http"):
                return redirect(cached_pdf)
            # If we have a cached storage path, get the URL
            else:
                supabase = current_app.supabase
                url_res = supabase.storage.from_(supabase_bucket_name).get_public_url(cached_pdf)
                return redirect(url_res)

        html_content = generate_resume_html(data)
        increment = (len(data.get('experience', [])) / 5) * 50
        final_css = css_height_calc(
            html_content,
            get_default_css,
            data.get('personal', {}).get('email'),
            'andromeda',
            0,
            max_attempts,
            increment
        )

        pdf_path = upload_pdf_to_supabase(name, "andromeda", html_content, final_css)

        combined_data = {
            "template": "andromeda",
            "resume_data": data
        }

        redis_client = current_app.redis_client
        data_str = json.dumps(combined_data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        redis_client.set(f"{data['personal']['email']}_data_hash_andromeda", data_hash)
        redis_client.set(f"{data['personal']['email']}_storage_path_andromeda", pdf_path)

        supabase = current_app.supabase
        url_res = supabase.storage.from_(supabase_bucket_name).get_public_url(pdf_path)
        return redirect(url_res)

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
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/><link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;1,100;1,200;1,300;1,400;1,500;1,600;1,700&display=swap" rel="stylesheet">
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
    '''
    for social in resume_data.get('socials', []):
        html += f'''
            {f'<a href="{social.get("link")}"><i class="fab fa-{social.get("slug")} fa-xl"></i></a>' if social.get('link') else ''}
        '''


    html += f'''
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
    if resume_data.get('experience') and len(resume_data['experience']) <= 4:
        if resume_data.get('education'):
            html += '''
                    <section class="section">
                        <h2 class="section-title">Education</h2>
                        <div class="section-content">
            '''
            
            for edu in resume_data.get('education', []):
                html += f'''
                            <div class="item" style="margin-bottom:1.5rem;">
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

    # Languages
    if resume_data.get('experience') and len(resume_data['experience']) <= 2:
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
    
    # Close left column
    html += '''
                </div>
                
                <!-- Right Column: Skills, Languages, Certifications, Awards, Interests, References -->
                <div class="right-column">
    '''
    
    # Education
    if resume_data.get('experience') and len(resume_data['experience']) > 4:
        if resume_data.get('education'):
            html += '''
                    <section class="section">
                        <h2 class="section-title">Education</h2>
                        <div class="section-content">
            '''
            
            for edu in resume_data.get('education', []):
                html += f'''
                            <div class="item" style="margin-bottom:1.5rem;">
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

    # Skills
    if resume_data.get('skills'):
        if len(resume_data['skills']):
            html += '''
                <section class="section">
                    <h2 class="section-title">Skills</h2>
                    <div class="section-content">
            '''
            for skill in resume_data.get('skills', []):
                html += f'''
                    <div class="skill-group">
                        <h3 class="skill-group-title">{skill.get('name')}</h3>
                        <div class="skill-keywords">
                '''
                for keyword in skill.get('keywords', []):
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
    if len(resume_data['experience']) > 2:
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
                                    <div class="item-date" style="margin-top:-0.85rem;">{format_date(award.get('date', ''))}</div>
                                </div>
                                {f'<div class="item-description"><p>{award.get("description", "")}</p></div>' if award.get('description') else ''}
                            </div>
            '''
            
        html += '''
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
                                    {f'<p>Email: {ref.get("email")}</p>' if ref.get("email") else ''}
                                    {f'<p>Phone: {ref.get("phone")}</p>' if ref.get("phone") else ''}
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


def get_default_css(dynamic_height=None):
    height = f"{dynamic_height}pt" if dynamic_height else "1009pt"
    """Return default CSS for the resume based on Modern template"""
    css = f"""
    @page {{
        margin: 0;
        size: 612pt {height};
    }}
    """

    css += """
    * {
        box-sizing: border-box;
    }

    body {
        margin: 0;
        padding: 0;
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
        margin-left: 2px
    }

    .social-links a {
        color: white;
        text-decoration: none;
        border-radius: 4px;
        font-size: 0.9rem;
        margin-right: 3px;
        transition: background-color 0.2s;
    }

    .social-links a:hover {
        background-color: rgba(255, 255, 255, 0.3);
    }

    .social-links a img.link-img {
        width: 20px;
        height: 20px;
    }

    /* Main Content Layout */
    .main-content {
        display: flex;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 0;
    }

    .left-column {
        flex: 2;
        padding-right: 1.5rem;
    }

    .right-column {
        flex: 1.5;
        padding-left: 0.5rem;
    }

    /* Summary Styles */
    .summary {
        margin-top: -0.5rem;
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
        margin-bottom: 0.70rem;
    }

    .item-title {
        margin-top: -0.70rem;
        font-size: 1.15rem;
        font-weight: 600;
        color: #1f2937;
    }

    .item-subtitle {
        font-size: 1rem;
        color: #4b5563;
        margin-bottom: 0.25rem;
        margin-top: -1rem;
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
        line-height: 1.5;
        margin-top: -0.5rem;
    }

    ul.list-disc.ml-3,
    ul.ml-3 {
        margin-left: 0 !important;
        padding-left: 1.2em; /* keep bullet indent, but not excessive */
    }
    ul.list-disc {
        list-style-type: disc;
    }

    ul.list-disc li {
        margin-top: 0;           /* No extra space before the first bullet */
        margin-bottom: 0.5em;    /* Small space after each bullet */
    }

    ul.list-disc li:not(:first-child) {
        margin-top: -6px;        /* Reduce space between bullets after the first */
    }
    ul.list-disc li p {
        margin: 0;
        padding: 0;
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
        padding-left: 0.25rem;
        border-radius: 6px;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }

    .reference-contact {
        font-size: 0.9rem;
        color: #4b5563;
    }
    
    .reference-contact p {
        margin: 2px 0;
    }
    """
    return css
