# apollo
import os
import sys
from flask import redirect, request, jsonify, current_app
import logging
from utils.apollo_helper import buff_calc
from utils.helper import css_height_calc, data_caching, format_date, format_description, upload_pdf_to_supabase, increment_calc
import json
import hashlib

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

max_attempts = 100 # maximum attempts in loop
supabase_bucket_name = os.getenv("SUPABASE_BUCKET_NAME", "bucket_name")

def generate_pdf():
    """Generate a PDF resume from the provided data and return it as a preview (greek-themed style)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No resume data provided'}), 400
        
        name = data.get('personal', {}).get('name')
        cached_pdf = data_caching(data, "apollo")
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
        buffer = buff_calc(data)
        increment = increment_calc(data, 10)
        final_css = css_height_calc(html_content, get_apollo_css, data.get('personal', {}).get('email'), 'apollo', buffer, max_attempts, increment)
        pdf_path = upload_pdf_to_supabase(name, "apollo", html_content, final_css)

        combined_data = {
            "template": "apollo",
            "resume_data": data
        }

        # Cache new data and PDF path
        redis_client = current_app.redis_client
        data_str = json.dumps(combined_data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        redis_client.set(f"{data['personal']['email']}_data_hash_apollo", data_hash)
        redis_client.set(f"{data['personal']['email']}_storage_path_apollo", pdf_path)

        supabase = current_app.supabase
        url_res = supabase.storage.from_(supabase_bucket_name).get_public_url(pdf_path)
        return redirect(url_res)
        # return jsonify({'html': html_content})

    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def generate_resume_html(resume_data):
    """Generate HTML content for a clean, modern two-column resume template with Apollo theme"""
    personal = resume_data.get('personal', {})
    education = resume_data.get('education', [])
    skills = resume_data.get('skills', [])
    certifications = resume_data.get('certifications', [])
    languages = resume_data.get('languages', [])
    socials = resume_data.get('socials', [])

    # Contact & Socials
    contact_html = ''
    if personal.get('website'):
        contact_html += f'<div class="sidebar-contact-item"><i class="icon-globe fas fa-globe"></i><span class="contact-text"><a href="{personal.get("website", {}).get("link")}" target="_blank">{personal.get("website", {}).get("name")}</a></span></div>'
    if personal.get('email'):
        contact_html += f'<div class="sidebar-contact-item"><i class="icon-email fas fa-envelope"></i><a href="mailto:{personal.get("email", "")}" class="contact-text">{personal.get("email", "")}</a></div>'
    if personal.get('location'):
        contact_html += f'<div class="sidebar-contact-item"><i class="icon-location fas fa-map-marker-alt"></i><span class="contact-text">{personal.get("location", "")}</span></div>'
    # Social links
    if socials:
        for social in socials:
            if social.get('link'):
                contact_html += f'<div class="sidebar-contact-item"><i class="icon-social fab fa-{social.get("slug")}"></i><a href="{social.get("link")}" class="contact-text">{social.get("name", social.get("slug", ""))}</a></div>'

    # Education
    education_html = ''
    if education:
        education_html += '<div class="sidebar-section"><div class="sidebar-section-title">EDUCATION</div>'
        for edu in education:
            education_html += f'''<div class="sidebar-edu-item">
                <div class="sidebar-edu-degree">{edu.get("degree", "")}</div>
                <div class="sidebar-edu-school">{edu.get("institution", "")}</div>
                <div class="sidebar-edu-date">{format_date(edu.get("startDate", ""))} - {format_date(edu.get("endDate", "")) if edu.get("endDate") else "Present"}</div>
            </div>'''
        education_html += '</div>'

    # Skills
    all_keywords = []
    for skill in skills:
        all_keywords.extend(skill.get('keywords', []))
    skills_html = ''
    if all_keywords:
        skills_html = '<div class="sidebar-section"><div class="sidebar-section-title">SKILLS</div><ul class="sidebar-skills">' + ''.join([f'<li>{skill}</li>' for skill in all_keywords]) + '</ul></div>'

    # Projects
    projects_html = ''
    if resume_data.get('projects'):
        projects_html += '<div class="sidebar-section"><div class="sidebar-section-title">PROJECTS</div>'
        for project in resume_data.get('projects', []):
            tech_tags = ', '.join(project.get('technologies', []))
            projects_html += f'''<div class="sidebar-project-item">
                <div class="sidebar-project-title">{project.get("title", "")}</div>
                <div class="sidebar-project-tech">{tech_tags}</div>
                <div class="sidebar-project-desc">{format_description(project.get("description", ""))}</div>
            </div>'''
        projects_html += '</div>'

    # Certifications
    certifications_html = ''
    if certifications:
        certifications_html += '<div class="sidebar-section"><div class="sidebar-section-title">CERTIFICATIONS</div>'
        for cert in certifications:
            certifications_html += f'''<div class="sidebar-cert-item">
                <div class="sidebar-cert-name">{cert.get("name", "")}</div>
                <div class="sidebar-cert-org">{cert.get("issuingOrganization", "")}</div>
                <div class="sidebar-cert-date">{format_date(cert.get("date", ""))}</div>
            </div>'''
        certifications_html += '</div>'

    # Languages
    languages_html = ''
    if languages:
        languages_html = '<div class="sidebar-section"><div class="sidebar-section-title">LANGUAGES</div><ul class="sidebar-languages">' + ''.join([f'<li>{lang}</li>' for lang in languages]) + '</ul></div>'

    # Sidebar HTML
    sidebar_html = f'''
    <aside class="resume-sidebar">
        <div class="sidebar-header">
            <div class="sidebar-name">{personal.get('name', '')}</div>
            <div class="sidebar-title">{personal.get('headline', '')}</div>
        </div>
        <div class="sidebar-contact">{contact_html}</div>
        {education_html}
        {skills_html}
        {projects_html}
        {certifications_html}
        {languages_html}
    </aside>
    '''

    # Main Content Sections
    # Profile (Summary)
    summary_html = ''
    if resume_data.get('summary'):
        summary_html = f'<div class="main-section"><div class="main-section-title">PROFILE</div><div class="main-summary">{format_description(resume_data.get("summary", ""))}</div></div>'

    # Work Experience
    experience_html = ''
    if resume_data.get('experience'):
        experience_html += '<div class="main-section"><div class="main-section-title">WORK EXPERIENCE</div>'
        for job in resume_data.get('experience', []):
            experience_html += f'''<div class="main-exp-item">
                <div class="main-exp-header">
                    <div class="main-exp-title">{job.get("title", "")}</div>
                    <div class="main-exp-date">{format_date(job.get("startDate", ""))} - {format_date(job.get("endDate", "")) if job.get("endDate") else "Present"}</div>
                </div>
                <div class="main-exp-company">{job.get("company", "")}</div>
                <div class="main-exp-desc">{format_description(job.get("description", ""))}</div>
            </div>'''
        experience_html += '</div>'

    # Awards
    awards_html = ''
    if resume_data.get('awards'):
        awards_html += '<div class="main-section"><div class="main-section-title">AWARDS</div>'
        for award in resume_data.get('awards', []):
            awards_html += f'''<div class="main-exp-item">
                <div class="main-exp-header">
                    <div class="main-exp-title">{award.get("title", "")}</div>
                    <div class="main-exp-date">{format_date(award.get("date", ""))}</div>
                </div>
                <div class="main-exp-desc">{format_description(award.get("summary", ""))}</div>
            </div>'''
        awards_html += '</div>'

    # References
    references_html = ''
    if resume_data.get('references'):
        references_html += '<div class="main-section"><div class="main-section-title">REFERENCES</div>'
        for ref in resume_data.get('references', []):
            email = ref.get("email") or "-"
            phone = ref.get("phone") or "-"
            references_html += f'''<div class="main-exp-item">
                <div class="main-exp-title">{ref.get("name", "")}</div>
                <div class="main-exp-company">{ref.get("company", "")}</div>
                <div class="main-exp-desc">{email} | {phone}</div>
            </div>'''
        references_html += '</div>'

    # Main HTML
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{personal.get('name', 'Resume')}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Fugaz+One&display=swap" rel="stylesheet">
    </head>
    <body>
        <div class="resume-header">
            <div class="resume-header-content">
                <div class="resume-header-name">{personal.get('name', '')}</div>
                <div class="resume-header-title">{personal.get('headline', '')}</div>
            </div>
        </div>
        <div class="resume-main-container">
            {sidebar_html}
            <main class="resume-main-content">
                {summary_html}
                {experience_html}
                {awards_html}
                {references_html}
            </main>
        </div>
    </body>
    </html>
    '''

    return html

def get_apollo_css(dynamic_height=None):
    """Apollo-inspired CSS with golden hues and Greek aesthetics - FIXED VERSION"""
    height = f"{dynamic_height}pt" if dynamic_height else "1009pt"
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
        font-family: 'Fugaz One', Arial, sans-serif;
        color: #2c2418;
        background: linear-gradient(135deg, #f4f1e8 0%, #e8dcc0 100%);
        margin: 0;
        padding: 0;
        min-height: 100vh;
        font-size: 14px;
        line-height: 1.4;
    }

    .resume-header {
        background: linear-gradient(135deg, #c9aa71 0%, #b8956a 50%, #a67c52 100%);
        padding: 2rem 1rem 1.5rem 1rem;
        border-bottom: 3px solid #8b6914;
        text-align: center;
        position: relative;
        box-shadow: 0 4px 8px rgba(139, 105, 20, 0.2);
    }

    .resume-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.1) 50%, transparent 100%);
        pointer-events: none;
    }

    .resume-header-content {
        max-width: 900px;
        margin: 0 auto;
        position: relative;
        z-index: 1;
    }

    .resume-header-name {
        font-family: 'Fugaz One', sans-serif;
        font-size: 2.2rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: #fff;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 0.3rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }

    .resume-header-title {
        font-size: 1.1rem;
        color: #f5f0e1;
        font-weight: 300;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }

    .resume-main-container {
        display: flex;
        max-width: 1000px;
        margin: 0 auto;
        background: #fff;
        box-shadow: 0 8px 32px rgba(139, 105, 20, 0.15);
        border-radius: 0 0 12px 12px;
        overflow: hidden;
        min-height: calc(100vh - 180px);
    }

    .resume-sidebar {
        width: 280px;
        min-width: 280px;
        max-width: 280px;
        flex: 0 0 280px;
        background: #fff;
        padding: 1.5rem 1.2rem;
        overflow-wrap: break-word;
        word-wrap: break-word;
        hyphens: auto;
    }

    .sidebar-header {
        display: none;
    }

    .sidebar-contact {
        margin-bottom: 1.8rem;
    }

    .sidebar-contact-item {
        display: flex;
        align-items: flex-start;
        font-size: 0.85rem;
        color: #3d3425;
        margin-bottom: 0.9rem;
        gap: 0.75rem;
        line-height: 1.3;
    }

    .sidebar-contact-item i {
        color: #b8956a;
        min-width: 16px;
        width: 16px;
        text-align: center;
        margin-top: 0.1rem;
        flex-shrink: 0;
    }

    .sidebar-contact-item .contact-text,
    .sidebar-contact-item a {
        color: #3d3425;
        text-decoration: none;
        word-wrap: break-word;
        word-break: break-all;
        overflow-wrap: break-word;
        hyphens: auto;
        flex: 1;
        line-height: 1.3;
        min-width: 0;
    }

    .sidebar-contact-item a:hover {
        color: #8b6914;
        text-decoration: underline;
    }

    .sidebar-section {
        margin-bottom: 1.8rem;
    }

    .sidebar-section:last-child {
        margin-bottom: 0;
    }

    .sidebar-section-title {
        font-family: 'Fugaz One', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: #8b6914;
        margin-bottom: 0.9rem;
        letter-spacing: 0.04em;
        border-bottom: 2px solid #d4c5a0;
        padding-bottom: 0.4rem;
        text-transform: uppercase;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.2;
    }

    .sidebar-edu-item {
        margin-bottom: 1.2rem;
        background: rgba(255, 255, 255, 0.6);
        padding: 0.9rem;
        border-radius: 6px;
        border-left: 3px solid #c9aa71;
    }

    .sidebar-edu-item:last-child {
        margin-bottom: 0;
    }

    .sidebar-edu-degree {
        font-weight: 700;
        color: #2c2418;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.2;
    }

    .sidebar-edu-school {
        font-size: 0.8rem;
        color: #5a4d3a;
        margin-bottom: 0.3rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.2;
    }

    .sidebar-edu-date {
        font-size: 0.75rem;
        color: #8b7355;
        font-style: italic;
        word-wrap: break-word;
        overflow-wrap: break-word;
        line-height: 1.2;
    }

    .sidebar-skills, .sidebar-languages {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .sidebar-skills li, .sidebar-languages li {
        font-size: 0.75rem;
        color: #3d3425;
        background: rgba(201, 170, 113, 0.25);
        padding: 0.4rem 0.7rem;
        border-radius: 12px;
        border: 1px solid #d4c5a0;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.2;
        flex-shrink: 0;
        max-width: 100%;
    }

    .sidebar-cert-item {
        margin-bottom: 1.1rem;
        background: rgba(255, 255, 255, 0.5);
        padding: 0.8rem;
        border-radius: 6px;
        border-left: 3px solid #b8956a;
    }

    .sidebar-cert-item:last-child {
        margin-bottom: 0;
    }

    .sidebar-cert-name {
        font-weight: 600;
        color: #2c2418;
        font-size: 0.82rem;
        margin-bottom: 0.3rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.2;
    }

    .sidebar-cert-org {
        font-size: 0.78rem;
        color: #5a4d3a;
        margin-bottom: 0.3rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.2;
    }

    .sidebar-cert-date {
        font-size: 0.74rem;
        color: #8b7355;
        font-style: italic;
        word-wrap: break-word;
        overflow-wrap: break-word;
        line-height: 1.2;
    }

    .sidebar-project-item {
        margin-bottom: 1.1rem;
        background: rgba(255, 255, 255, 0.5);
        padding: 0.8rem;
        border-radius: 6px;
        border-left: 3px solid #b8956a;
    }

    .sidebar-project-item:last-child {
        margin-bottom: 0;
    }

    .sidebar-project-title {
        font-weight: 600;
        color: #2c2418;
        font-size: 0.82rem; /* match .sidebar-cert-name */
        margin-bottom: 0.3rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.2;
    }

    .sidebar-project-tech {
        font-size: 0.78rem; /* match .sidebar-cert-org */
        color: #5a4d3a;
        margin-bottom: 0.3rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.2;
        font-style: italic;
    }

    .sidebar-project-desc {
        font-size: 0.74rem; /* match .sidebar-cert-date */
        color: #8b7355;
        word-wrap: break-word;
        overflow-wrap: break-word;
        line-height: 1.2;
    }

    .resume-main-content {
        flex: 1;
        padding: 1.3rem 1.5rem;
        background: #fff;
        min-width: 0;
        overflow-wrap: break-word;
        word-wrap: break-word;
        hyphens: auto;
        border-left: 2px solid #d4c5a0;
    }

    .main-section {
        margin-bottom: 2.2rem;
    }

    .main-section:last-child {
        margin-bottom: 0;
    }

    .main-section-title {
        font-family: 'Fugaz One', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #8b6914;
        margin-bottom: 1.3rem;
        position: relative;
        padding-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.025em;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.2;
    }

    .main-section-title::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #c9aa71 0%, #d4c5a0 100%);
    }

    .main-summary {
        font-size: 0.9rem;
        color: #3d3425;
        line-height: 1.6;
        text-align: justify;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }

    .main-exp-item {
        margin-bottom: 1.5rem;
        padding-bottom: 1.2rem;
        border-bottom: 1px solid #f0ead6;
        position: relative;
    }

    .main-exp-item:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }

    .main-exp-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.5rem;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .main-exp-title {
        font-weight: 700;
        color: #2c2418;
        font-size: 0.95rem;
        flex: 1;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.3;
        min-width: 0;
    }

    .main-exp-date {
        font-size: 0.8rem;
        color: #8b7355;
        font-style: italic;
        text-align: right;
        flex-shrink: 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
        line-height: 1.3;
    }

    .main-exp-company {
        font-size: 0.85rem;
        color: #b8956a;
        font-weight: 600;
        margin-bottom: 0.6rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        line-height: 1.3;
    }

    .main-exp-desc {
        font-size: 0.82rem;
        color: #3d3425;
        line-height: 1.5;
        text-align: justify;
        word-wrap: break-word;
        word-break: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }

    /* List formatting improvements */
    ul.list-disc,
    ul.ml-3 {
        margin-left: 0 !important;
        padding-left: 1.5em;
        margin-top: 0.5em;
        margin-bottom: 0.5em;
    }
    
    ul.list-disc {
        list-style-type: disc;
    }

    ul.list-disc li {
        margin-bottom: 0.4em;
        line-height: 1.4;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }

    ul.list-disc li:last-child {
        margin-bottom: 0;
    }
    
    ul.list-disc li p {
        margin: 0;
        padding: 0;
    }

    /* Responsive design improvements */
    @media (max-width: 1024px) {
        .resume-main-container {
            max-width: 95%;
            margin: 0 2.5%;
        }
        
        .resume-sidebar {
            width: 260px;
            min-width: 260px;
            max-width: 260px;
            flex: 0 0 260px;
            padding: 1.3rem 1rem;
        }
        
        .resume-main-content {
            padding: 1.5rem 1.5rem;
        }
    }

    @media (max-width: 768px) {
        .resume-main-container {
            flex-direction: column;
            margin: 0 1rem;
        }
        
        .resume-sidebar {
            width: 100%;
            min-width: auto;
            max-width: none;
            flex: none;
            border-right: none;
            border-bottom: 2px solid #d4c5a0;
            padding: 1.5rem;
        }
        
        .resume-main-content {
            padding: 1.5rem;
        }
        
        .main-exp-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.3rem;
        }
        
        .main-exp-date {
            text-align: left;
        }
        
        .sidebar-skills, .sidebar-languages {
            gap: 0.4rem;
        }
        
        .sidebar-skills li, .sidebar-languages li {
            font-size: 0.72rem;
            padding: 0.35rem 0.6rem;
        }
        
        .resume-header-name {
            font-size: 1.8rem;
        }
        
        .resume-header-title {
            font-size: 1rem;
        }
    }

    @media (max-width: 480px) {
        .resume-header {
            padding: 1.5rem 0.5rem 1rem 0.5rem;
        }
        
        .resume-header-name {
            font-size: 1.6rem;
            letter-spacing: 0.04em;
        }
        
        .resume-header-title {
            font-size: 0.9rem;
        }
        
        .resume-sidebar,
        .resume-main-content {
            padding: 1rem;
        }
        
        .sidebar-contact-item {
            font-size: 0.8rem;
        }
        
        .main-exp-desc {
            font-size: 0.8rem;
        }
    }

    @media print {
        body {
            background: white;
            font-size: 12px;
        }
        
        .resume-header {
            background: linear-gradient(135deg, #c9aa71 0%, #b8956a 100%);
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
            page-break-inside: avoid;
        }
        
        .resume-main-container {
            box-shadow: none;
            page-break-inside: avoid;
        }
        
        .main-section {
            page-break-inside: avoid;
        }
        
        .main-exp-item {
            page-break-inside: avoid;
        }
        
        .sidebar-skills, .sidebar-languages {
            gap: 0.3rem;
        }
        
        .sidebar-skills li, .sidebar-languages li {
            font-size: 0.7rem;
            padding: 0.3rem 0.5rem;
        }
    }
    """
    return css