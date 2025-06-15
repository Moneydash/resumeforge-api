# artemis
import os
from flask import redirect, request, jsonify, current_app
import logging
from utils.artemis_helper import buff_calc
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
        cached_pdf = data_caching(data, "artemis")
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
        increment = increment_calc(data, 15)
        final_css = css_height_calc(html_content, get_artemis_css, data.get('personal', {}).get('email'), 'artemis', buffer, max_attempts, increment)
        pdf_path = upload_pdf_to_supabase(name, "artemis", html_content, final_css)

        combined_data = {
            "template": "artemis",
            "resume_data": data
        }

        # Cache new data and PDF path
        redis_client = current_app.redis_client
        data_str = json.dumps(combined_data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        redis_client.set(f"{data['personal']['email']}_data_hash_artemis", data_hash)
        redis_client.set(f"{data['personal']['email']}_storage_path_artemis", pdf_path)

        supabase = current_app.supabase
        url_res = supabase.storage.from_(supabase_bucket_name).get_public_url(pdf_path)
        return redirect(url_res)
        # return jsonify({'html': html_content})

    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def generate_resume_html(resume_data):
    """Generate HTML content for a clean, modern two-column resume template optimized for WeasyPrint"""
    personal = resume_data.get('personal', {})
    education = resume_data.get('education', [])
    skills = resume_data.get('skills', [])
    certifications = resume_data.get('certifications', [])
    languages = resume_data.get('languages', [])
    socials = resume_data.get('socials', [])

    # Contact information for sidebar
    contact_html = ''
    if personal.get('location'):
        contact_html += f'<div class="sidebar-contact-item"><i class="fas fa-location-dot"></i><span class="contact-text">{personal.get("location", "")}</span></div>'
    if personal.get('email'):
        contact_html += f'<div class="sidebar-contact-item"><i class="fas fa-envelope"></i><a href="mailto:{personal.get("email", "")}" class="contact-text">{personal.get("email", "")}</a></div>'
    if personal.get('website'):
        contact_html += f'<div class="sidebar-contact-item"><i class="fas fa-globe"></i><span class="contact-text"><a href="{personal.get("website", {}).get("link")}" target="_blank">{personal.get("website", {}).get("name")}</a></span></div>'

    # Social links for header
    social_links_html = ''
    if socials:
        social_links_html = '<div class="social-links">'
        for social in socials:
            if social.get('link'):
                icon_class = f"fab fa-{social.get('slug', '')}"
                social_links_html += f'<a href="{social.get("link")}" target="_blank"><i class="{icon_class}"></i></a>'
        social_links_html += '</div>'

    # Education section
    education_html = ''
    if education:
        education_html += '<div class="sidebar-section"><div class="sidebar-section-title">Education</div>'
        for edu in education:
            education_html += f'''<div class="sidebar-edu-item">
                <div class="sidebar-edu-degree">{edu.get("degree", "")}</div>
                <div class="sidebar-edu-school">{edu.get("institution", "")}</div>
                <div class="sidebar-edu-date">{format_date(edu.get("startDate", ""))} - {format_date(edu.get("endDate", "")) if edu.get("endDate") else "Present"}</div>
            </div>'''
        education_html += '</div>'

    # Skills section
    all_keywords = []
    for skill in skills:
        all_keywords.extend(skill.get('keywords', []))
    skills_html = ''
    if all_keywords:
        skills_html = '<div class="sidebar-section"><div class="sidebar-section-title">Skills</div><div class="sidebar-skills">' + ''.join([f'<span class="skill-tag">{skill}</span>' for skill in all_keywords]) + '</div></div>'

    # Projects section
    projects_html = ''
    if resume_data.get('projects'):
        projects_html += '<div class="sidebar-section"><div class="sidebar-section-title">Projects</div>'
        for project in resume_data.get('projects', []):
            tech_tags = ', '.join(project.get('technologies', []))
            projects_html += f'''<div class="sidebar-project-item">
                <div class="sidebar-project-title">{project.get("title", "")}</div>
                <div class="sidebar-project-desc">{format_description(project.get("description", ""))}</div>
                <div class="sidebar-project-tech">{tech_tags}</div>
            </div>'''
        projects_html += '</div>'

    # Certifications section
    certifications_html = ''
    if certifications:
        certifications_html += '<div class="sidebar-section"><div class="sidebar-section-title">Certifications</div>'
        for cert in certifications:
            certifications_html += f'''<div class="sidebar-cert-item">
                <div class="sidebar-cert-name">{cert.get("name", "")}</div>
                <div class="sidebar-cert-org">{cert.get("issuingOrganization", "")}</div>
                <div class="sidebar-cert-date">{format_date(cert.get("date", ""))}</div>
            </div>'''
        certifications_html += '</div>'

    # Languages section
    languages_html = ''
    if languages:
        languages_html = '<div class="sidebar-section"><div class="sidebar-section-title">Languages</div><div class="sidebar-languages">' + ''.join([f'<span class="language-tag">{lang}</span>' for lang in languages]) + '</div></div>'

    # Main Content Sections
    # Profile (Summary)
    summary_html = ''
    if resume_data.get('summary'):
        summary_html = f'<div class="main-section"><div class="main-section-title">Summary</div><div class="main-summary">{format_description(resume_data.get("summary", ""))}</div></div>'

    # Work Experience
    experience_html = ''
    if resume_data.get('experience'):
        experience_html += '<div class="main-section"><div class="main-section-title">Experience</div>'
        for job in resume_data.get('experience', []):
            experience_html += f'''<div class="main-exp-item">
                <div class="main-exp-header">
                    <div class="main-exp-left">
                        <div class="main-exp-title">{job.get("title", "")}</div>
                        <div class="main-exp-company">{job.get("company", "")}</div>
                    </div>
                    <div class="main-exp-date">{format_date(job.get("startDate", ""))} - {format_date(job.get("endDate", "")) if job.get("endDate") else "Present"}</div>
                </div>
                <div class="main-exp-desc">{format_description(job.get("description", ""))}</div>
            </div>'''
        experience_html += '</div>'

    # Awards
    awards_html = ''
    if resume_data.get('awards'):
        awards_html += '<div class="main-section"><div class="main-section-title">Awards</div>'
        for award in resume_data.get('awards', []):
            awards_html += f'''<div class="main-exp-item">
                <div class="main-exp-header">
                    <div class="main-exp-left">
                        <div class="main-exp-title">{award.get("title", "")}</div>
                    </div>
                    <div class="main-exp-date">{format_date(award.get("date", ""))}</div>
                </div>
                <div class="main-exp-desc">{format_description(award.get("summary", ""))}</div>
            </div>'''
        awards_html += '</div>'

    # References
    references_html = ''
    if resume_data.get('references'):
        references_html += '<div class="main-section"><div class="main-section-title">References</div>'
        for ref in resume_data.get('references', []):
            email = ref.get("email") or "-"
            phone = ref.get("phone") or "-"
            references_html += f'''<div class="main-exp-item">
                <div class="main-exp-title">{ref.get("name", "")}</div>
                <div class="main-exp-company">{ref.get("company", "")}</div>
                <div class="main-exp-desc">{email} | {phone}</div>
            </div>'''
        references_html += '</div>'

    # Main HTML - Optimized for WeasyPrint
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
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap" rel="stylesheet">
    </head>
    <body>
        <div class="resume-container">
            <div class="resume-body">
                <div class="resume-left-section">
                    <div class="resume-header">
                        <div class="resume-header-content">
                            <div class="resume-header-name">{personal.get('name', '')}</div>
                            <div class="resume-header-title">{personal.get('headline', '')}</div>
                            {social_links_html}
                        </div>
                    </div>
                    <main class="resume-main-content">
                        {summary_html}
                        {experience_html}
                        {awards_html}
                        {references_html}
                    </main>
                </div>
                <aside class="resume-sidebar">
                    <div class="sidebar-section">
                        <div class="sidebar-section-title">Contact</div>
                        <div class="sidebar-contact">{contact_html}</div>
                    </div>
                    {education_html}
                    {skills_html}
                    {projects_html}
                    {certifications_html}
                    {languages_html}
                </aside>
            </div>
        </div>
    </body>
    </html>
    '''

    return html


def get_artemis_css(dynamic_height=None):
    """CSS optimized for WeasyPrint with proper text wrapping and layout"""
    height = f"{dynamic_height}pt" if dynamic_height else "1009pt"
    
    css = f"""
    @page {{
        margin: 0;
        size: 612pt {height};
    }}
    
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    
    body {{
        font-family: 'Playfair Display', serif;
        color: #000;
        background: #fff;
        font-size: 12px;
        line-height: 1.4;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .resume-container {{
        width: 100%;
        background: #fff;
        min-height: 100vh;
    }}

    .resume-body {{
        display: table;
        width: 100%;
        min-height: 100vh;
        table-layout: fixed;
    }}

    .resume-left-section {{
        display: table-cell;
        width: 65%;
        vertical-align: top;
        position: relative;
    }}

    .resume-sidebar {{
        display: table-cell;
        width: 35%;
        background: #d9d9d9;
        padding: 20px;
        vertical-align: top;
        word-wrap: break-word;
        overflow-wrap: break-word;
        height: {height}
    }}

    .resume-header {{
        background: #1b2e2b;
        padding: 30px 40px;
        text-align: center;
        color: white;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .resume-header-content {{
        width: 100%;
    }}

    .resume-header-name {{
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        font-weight: bold;
        letter-spacing: 0.02em;
        margin-bottom: 8px;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .resume-header-title {{
        font-size: 1.1rem;
        font-weight: normal;
        letter-spacing: 0.03em;
        margin-bottom: 15px;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .social-links {{
        display: inline-block;
        text-align: center;
        margin-top: 15px;
    }}

    .social-links a {{
        color: white;
        font-size: 1.3rem;
        text-decoration: none;
        margin: 0 8px;
        display: inline-block;
    }}

    .resume-main-content {{
        padding: 25px 20px;
        background: #fff;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .main-section {{
        margin-bottom: 30px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .main-section:last-child {{
        margin-bottom: 0;
    }}

    .main-section-title {{
        font-family: 'Playfair Display', serif;
        font-size: 1.2rem;
        font-weight: bold;
        color: #000;
        margin-bottom: 15px;
        border-bottom: 2px solid #000;
        padding-bottom: 5px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .main-summary {{
        font-size: 0.95rem;
        color: #333;
        line-height: 1.5;
        text-align: justify;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .main-exp-item {{
        margin-bottom: 25px;
        padding-bottom: 20px;
        border-bottom: 1px solid #e0e0e0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .main-exp-item:last-child {{
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }}

    .main-exp-header {{
        margin-bottom: 12px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .main-exp-left {{
        margin-bottom: 8px;
    }}

    .main-exp-title {{
        font-weight: bold;
        color: #000;
        font-size: 1.05rem;
        margin-bottom: 4px;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .main-exp-company {{
        font-size: 0.95rem;
        color: #666;
        font-style: italic;
        margin-bottom: 4px;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .main-exp-date {{
        font-size: 0.85rem;
        color: #666;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .main-exp-desc {{
        font-size: 0.9rem;
        color: #333;
        line-height: 1.5;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .main-exp-desc ul {{
        margin: 8px 0;
        padding-left: 18px;
    }}

    .main-exp-desc li {{
        margin-bottom: 6px;
        line-height: 1.4;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-section {{
        margin-bottom: 25px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-section:last-child {{
        margin-bottom: 0;
    }}

    .sidebar-section-title {{
        font-family: 'Playfair Display', serif;
        font-size: 1rem;
        font-weight: bold;
        color: #000;
        margin-bottom: 12px;
        border-bottom: 2px solid #000;
        padding-bottom: 4px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-contact {{
        margin-bottom: 0;
    }}

    .sidebar-contact-item {{
        display: block;
        font-size: 0.85rem;
        color: #333;
        margin-bottom: 10px;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-contact-item i {{
        color: #666;
        width: 14px;
        display: inline-block;
        margin-right: 6px;
    }}

    .sidebar-contact-item .contact-text,
    .sidebar-contact-item a {{
        color: #333;
        text-decoration: none;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-edu-item {{
        margin-bottom: 18px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-edu-item:last-child {{
        margin-bottom: 0;
    }}

    .sidebar-edu-degree {{
        font-weight: bold;
        color: #000;
        font-size: 0.9rem;
        margin-bottom: 4px;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .sidebar-edu-school {{
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 3px;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .sidebar-edu-date {{
        font-size: 0.8rem;
        color: #888;
        font-style: italic;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-skills {{
        line-height: 1.8;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .skill-tag {{
        background: #1b2e2b;
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: normal;
        display: inline-block;
        margin: 2px 4px 2px 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-project-item {{
        margin-bottom: 18px;
        padding-bottom: 12px;
        border-bottom: 1px solid #bbb;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-project-item:last-child {{
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }}

    .sidebar-project-title {{
        font-weight: bold;
        color: #000;
        font-size: 0.9rem;
        margin-bottom: 6px;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .sidebar-project-desc {{
        font-size: 0.8rem;
        color: #555;
        line-height: 1.4;
        margin-bottom: 6px;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .sidebar-project-tech {{
        font-size: 0.75rem;
        color: #888;
        font-style: italic;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-cert-item {{
        margin-bottom: 18px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-cert-item:last-child {{
        margin-bottom: 0;
    }}

    .sidebar-cert-name {{
        font-weight: bold;
        color: #000;
        font-size: 0.85rem;
        margin-bottom: 4px;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .sidebar-cert-org {{
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 3px;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
    }}

    .sidebar-cert-date {{
        font-size: 0.75rem;
        color: #888;
        font-style: italic;
        line-height: 1.3;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .sidebar-languages {{
        line-height: 1.8;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .language-tag {{
        background: #1b2e2b;
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: normal;
        display: inline-block;
        margin: 2px 4px 2px 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}
    """
    
    return css