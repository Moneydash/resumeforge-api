# athena
import os
from flask import redirect, request, jsonify, current_app
import logging
from utils.athena_helper import buff_calc
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
        cached_pdf = data_caching(data, "athena")
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
        final_css = css_height_calc(html_content, get_athena_css, data.get('personal', {}).get('email'), 'athena', buffer, max_attempts, increment)
        pdf_path = upload_pdf_to_supabase(name, "athena", html_content, final_css)

        combined_data = {
            "template": "athena",
            "resume_data": data
        }

        # Cache new data and PDF path
        redis_client = current_app.redis_client
        data_str = json.dumps(combined_data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        redis_client.set(f"{data['personal']['email']}_data_hash_athena", data_hash)
        redis_client.set(f"{data['personal']['email']}_storage_path_athena", pdf_path)

        supabase = current_app.supabase
        url_res = supabase.storage.from_(supabase_bucket_name).get_public_url(pdf_path)
        return redirect(url_res)

    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def generate_resume_html(resume_data):
    """Generate HTML content for a professional, Athena-inspired two-column resume template"""
    # Sidebar: Personal Info, Education, Skills, Projects, Certifications
    personal = resume_data.get('personal', {})
    education = resume_data.get('education', [])
    skills = resume_data.get('skills', [])
    
    contact_html = ''
    if personal.get('location'):
        contact_html += f'<div class="sidebar-contact-item"><i class="icon-location"></i><span>{personal.get("location", "")}</span></div>'
    if personal.get('phone'):
        contact_html += f'<div class="sidebar-contact-item"><i class="icon-phone"></i><span>{personal.get("phone", "")}</span></div>'
    if personal.get('email'):
        contact_html += f'<div class="sidebar-contact-item"><i class="icon-email"></i><a href="mailto:{personal.get("email", "")}">{personal.get("email", "")}</a></div>'
    if personal.get('website', {}).get('link'):
        contact_html += f'<div class="sidebar-contact-item"><i class="icon-website"></i><a href="{personal.get("website", {}).get("link", "")}">{personal.get("website", {}).get("name", personal.get("website", {}).get("link", ""))}</a></div>'

    # Education
    education_html = ''
    if education:
        education_html += '<div class="sidebar-section"><div class="sidebar-section-title">Education</div>'
        for edu in education:
            education_html += f'''
            <div class="sidebar-edu-item">
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
        skill_tags = ''.join([f'<span class="skill-tag">{skill}</span>' for skill in all_keywords])
        skills_html = f'<div class="sidebar-section"><div class="sidebar-section-title">Skills</div><div class="sidebar-skills">{skill_tags}</div></div>'

    # Projects - moved to sidebar
    projects_html = ''
    if resume_data.get('projects'):
        projects_html += '<div class="sidebar-section"><div class="sidebar-section-title">Key Projects</div>'
        for project in resume_data.get('projects', []):
            tech_tags = ''.join([f'<span class="sidebar-tech-tag">{tech}</span>' for tech in project.get('technologies', [])])
            projects_html += f'''
            <div class="sidebar-project-item">
                <div class="sidebar-project-title">{project.get("title", "")}</div>
                <div class="sidebar-project-desc">{format_description(project.get("description", ""))}</div>
                <div class="sidebar-tech-tags">{tech_tags}</div>
            </div>'''
        projects_html += '</div>'

    # Certifications - moved to sidebar
    certifications_html = ''
    if resume_data.get('certifications'):
        certifications_html += '<div class="sidebar-section"><div class="sidebar-section-title">Certifications</div>'
        for cert in resume_data.get('certifications', []):
            certifications_html += f'''
            <div class="sidebar-cert-item">
                <div class="sidebar-cert-name">{cert.get("name", "")}</div>
                <div class="sidebar-cert-org">{cert.get("issuingOrganization", "")}</div>
                <div class="sidebar-cert-date">{format_date(cert.get("date", ""))}</div>
            </div>'''
        certifications_html += '</div>'
    
    # Awards
    awards_html = ''
    if resume_data.get('awards'):
        awards_html += '<div class="sidebar-section"><div class="sidebar-section-title">Awards</div>'
        for award in resume_data.get('awards', []):
            awards_html += f'''
            <div class="sidebar-award-item">
                <div class="sidebar-award-title">{award.get("title", "")}</div>
                <div class="sidebar-award-date">{format_date(award.get("date", ""))}</div>
            </div>'''
        awards_html += '</div>'
    
    # Languages
    languages_html = ''
    if resume_data.get('languages'):
        language_tags = ''.join([f'<div class="sidebar-language-tag">{lang}</div>' for lang in resume_data.get('languages', [])])
        languages_html = f'<div class="sidebar-section"><div class="sidebar-section-title">Languages</div><div class="sidebar-languages">{language_tags}</div></div>'

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
        {awards_html}
        {languages_html}
    </aside>
    '''

    # Main Content Sections
    # Socials
    socials_html = ''
    if resume_data.get('socials'):
        socials_html = '<div class="main-section"><div class="main-section-title">Professional Links</div><div class="main-socials">'
        for social in resume_data.get('socials', []):
            if social.get('link'):
                socials_html += f'<a href="{social.get("link")}" class="main-social-link"><i class="fab fa-{social.get("slug")} fa-lg"></i></a>'
        socials_html += '</div></div>'

    # Summary
    summary_html = ''
    if resume_data.get('summary'):
        summary_html = f'<div class="main-section"><div class="main-section-title">Professional Summary</div><div class="main-summary">{format_description(resume_data.get("summary", ""))}</div></div>'

    # Experience
    experience_html = ''
    if resume_data.get('experience'):
        experience_html += '<div class="main-section"><div class="main-section-title">Professional Experience</div>'
        for job in resume_data.get('experience', []):
            experience_html += f'''
            <div class="main-exp-item">
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

    # References
    references_html = ''
    if resume_data.get('references'):
        references_html += '<div class="main-section"><div class="main-section-title">References</div>'
        for ref in resume_data.get('references', []):
            references_html += f'''
            <div class="main-exp-item">
                <div class="main-exp-header">
                    <div class="main-exp-left">
                        <div class="main-exp-title">{ref.get("name", "")}</div>
                        <div class="main-exp-company">{ref.get("company", "")}</div>
                    </div>
                </div>
                <div class="main-exp-desc">{format_description((ref.get("email", "-") or "-") + " | " + (ref.get("phone", "-") or "-"))}</div>
            </div>'''
        references_html += '</div>'

    # Complete HTML structure
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{resume_data.get('personal', {}).get('name', 'Resume')}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Lexend+Deca:wght@100..900&display=swap" rel="stylesheet">
    </head>
    <body>
        <div class="resume-container">
            <div class="resume-main-container">
                {sidebar_html}
                <main class="resume-main-content">
                    {socials_html}
                    {summary_html}
                    {experience_html}
                    {references_html}
                </main>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

def get_athena_css(dynamic_height=None):
    """Enhanced CSS with professional Athena-inspired Greek design theme"""
    height = f"{dynamic_height}pt" if dynamic_height else "auto"

    css = f'''
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
        font-family: 'Lexend Deca', Roboto, sans-serif;
        color: #2d3748;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 50%, #e2e8f0 100%);
        margin: 0;
        padding: 0;
        line-height: 1.6;
        font-weight: 400;
        min-height: 100vh;
    }}

    .resume-container {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1rem;
    }}

    .resume-main-container {{
        display: flex;
        background: #ffffff;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.05);
        border-radius: 0;
        overflow: hidden;
        position: relative;
        min-height: 800px;
    }}

    /* Athena-inspired accent line */
    .resume-main-container::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: linear-gradient(90deg, #2b6cb5 0%, #1e40af 25%, #3b82f6 50%, #60a5fa 75%, #93c5fd 100%);
        z-index: 10;
    }}

    /* Sidebar Styles */
    .resume-sidebar {{
        width: 320px;
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 30%, #2563eb 100%);
        color: #ffffff;
        padding: 1.5rem 1rem;
        position: relative;
        overflow: hidden;
        height: {height}
    }}

    /* Greek-inspired pattern overlay */
    .resume-sidebar::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            radial-gradient(circle at 20% 80%, rgba(255,255,255,0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(255,255,255,0.03) 0%, transparent 50%);
        pointer-events: none;
    }}

    .sidebar-header {{
        margin-bottom: 1.5rem;
        position: relative;
        z-index: 2;
        text-align: left;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.15);
    }}

    .sidebar-name {{
        font-family: 'Lexend Deca', Roboto, sans-serif;
        font-size: 1.75rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
        line-height: 1.2;
    }}

    .sidebar-title {{
        font-size: 0.9rem;
        color: #bfdbfe;
        font-weight: 400;
        letter-spacing: 0.025em;
        line-height: 1.4;
    }}

    .sidebar-contact {{
        margin-bottom: 1.5rem;
        position: relative;
        z-index: 2;
    }}

    .sidebar-contact-item {{
        display: flex;
        align-items: flex-start;
        font-size: 0.85rem;
        color: #e0e7ff;
        margin-bottom: 0.75rem;
        line-height: 1.4;
    }}

    .sidebar-contact-item i {{
        margin-right: 0.5rem;
        width: 16px;
        flex-shrink: 0;
        margin-top: 0.125rem;
    }}

    .sidebar-contact-item .icon-location::before {{ content: "📍"; font-size: 0.75rem; }}
    .sidebar-contact-item .icon-phone::before {{ content: "📞"; font-size: 0.75rem; }}
    .sidebar-contact-item .icon-email::before {{ content: "✉️"; font-size: 0.75rem; }}
    .sidebar-contact-item .icon-website::before {{ content: "🌐"; font-size: 0.75rem; }}

    .sidebar-contact-item span {{
        word-break: break-word;
    }}

    .sidebar-contact-item a {{
        color: #bfdbfe;
        text-decoration: none;
        transition: color 0.2s ease;
        word-break: break-word;
    }}

    .sidebar-contact-item a:hover {{
        color: #ffffff;
    }}

    .sidebar-section {{
        margin-bottom: 1.5rem;
        position: relative;
        z-index: 2;
    }}

    .sidebar-section-title {{
        font-family: 'Lexend Deca', Roboto, sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.75rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    .sidebar-section-title::after {{
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 25px;
        height: 1px;
        background: #93c5fd;
    }}

    .sidebar-edu-item {{
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .sidebar-edu-item:last-child {{
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }}

    .sidebar-edu-degree {{
        font-weight: 600;
        color: #ffffff;
        font-size: 0.85rem;
        margin-bottom: 0.25rem;
        line-height: 1.3;
    }}

    .sidebar-edu-school {{
        font-size: 0.75rem;
        color: #bfdbfe;
        margin-bottom: 0.25rem;
        line-height: 1.3;
    }}

    .sidebar-edu-date {{
        font-size: 0.7rem;
        color: #e0e7ff;
        font-weight: 300;
    }}

    .sidebar-skills {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.3rem;
    }}

    .skill-tag {{
        background: rgba(255, 255, 255, 0.12);
        color: #ffffff;
        padding: 0.3rem 0.6rem;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 500;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .skill-tag:hover {{
        background: rgba(255, 255, 255, 0.2);
    }}

    /* Sidebar Projects Styles */
    .sidebar-project-item {{
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .sidebar-project-item:last-child {{
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }}

    .sidebar-project-title {{
        font-weight: 600;
        color: #ffffff;
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
        line-height: 1.3;
    }}

    .sidebar-project-desc {{
        font-size: 0.75rem;
        color: #bfdbfe;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }}

    .sidebar-tech-tags {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.25rem;
    }}

    .sidebar-tech-tag {{
        background: rgba(147, 197, 253, 0.2);
        color: #93c5fd;
        padding: 0.2rem 0.5rem;
        border-radius: 8px;
        font-size: 0.65rem;
        font-weight: 500;
        border: 1px solid rgba(147, 197, 253, 0.3);
    }}

    /* Sidebar Certifications Styles */
    .sidebar-cert-item, .sidebar-award-item {{
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .sidebar-cert-item:last-child, .sidebar-award-item:last-child {{
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }}

    .sidebar-cert-name, .sidebar-award-title {{
        font-weight: 600;
        color: #ffffff;
        font-size: 0.85rem;
        margin-bottom: 0.25rem;
        line-height: 1.3;
    }}

    .sidebar-cert-org {{
        font-size: 0.75rem;
        color: #bfdbfe;
        margin-bottom: 0.25rem;
        line-height: 1.3;
    }}

    .sidebar-cert-date, .sidebar-award-date {{
        font-size: 0.7rem;
        color: #e0e7ff;
        font-weight: 300;
    }}

    /* Main Content Styles */
    .resume-main-content {{
        flex: 1;
        padding: 2.5rem 2rem;
        background: #ffffff;
    }}

    .main-section {{
        margin-bottom: 2rem;
    }}

    .main-section:last-child {{
        margin-bottom: 0;
    }}

    .main-section-title {{
        font-family: 'Lexend Deca', Roboto, sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 1.25rem;
        position: relative;
        padding-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }}

    .main-section-title::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 1px;
        background: linear-gradient(90deg, #2563eb 0%, rgba(37, 99, 235, 0.2) 100%);
    }}

    .main-socials {{
        display: flex;
        gap: 1rem;
        margin-bottom: 0.35rem;
        margin-left: 3px;
    }}

    .main-social-link {{
        color: #2563eb;
        text-decoration: none;
        transition: all 0.2s ease;
        font-size: 0.85rem;
        margin-right: 0.25rem;
    }}

    .main-social-link:hover {{
        background: #2563eb;
        color: #ffffff;
        border-color: #2563eb;
    }}

    .main-summary {{
        font-size: 0.75rem;
        color: #4b5563;
        line-height: 1.7;
        text-align: justify;
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 6px;
        border-left: 4px solid #2563eb;
    }}

    .main-exp-item {{
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e5e7eb;
        position: relative;
    }}

    .main-exp-item:last-child {{
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }}

    .main-exp-header {{
        margin-top: -0.3rem;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
        gap: 1rem;
    }}

    .main-exp-left {{
        flex: 1;
    }}

    .main-exp-title {{
        font-size: 1rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.25rem;
        line-height: 1.3;
    }}

    .main-exp-company {{
        font-size: 0.95rem;
        color: #2563eb;
        font-weight: 500;
        font-style: italic;
    }}

    .main-exp-date {{
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 500;
        white-space: nowrap;
        background: #f3f4f6;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        align-self: flex-start;
    }}

    .main-exp-desc {{
        font-size: 0.9rem;
        color: #4b5563;
        line-height: 1.6;
        margin-top: -0.25rem;
        text-align: justify;
        margin-bottom: 0.5rem;
    }}

    .tech-tags {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.75rem;
    }}

    .sidebar-languages {{
        display: block;
    }}

    .tech-tag, .sidebar-language-tag {{
        background: #2563eb;
        color: #ffffff;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }}

    .sidebar-language-tag {{
        background: #059669;
        margin-bottom: 0.3rem;
        margin-right: 5px;
        display: inline-block;
        width: auto;
    }}

    /* Responsive Design */
    @media (max-width: 1024px) {{
        .resume-container {{
            padding: 0 0.5rem;
        }}
        
        .resume-main-content {{
            padding: 2rem 1.5rem;
        }}
        
        .resume-sidebar {{
            width: 300px;
            padding: 1.5rem 1rem;
        }}
    }}

    @media (max-width: 768px) {{
        body {{
            padding: 1rem 0;
        }}
        
        .resume-main-container {{
            flex-direction: column;
            margin: 0;
        }}
        
        .resume-sidebar {{
            width: 100%;
            padding: 1.5rem;
        }}
        
        .resume-main-content {{
            padding: 1.5rem;
        }}
        
        .main-exp-header {{
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }}
        
        .main-exp-date {{
            align-self: flex-start;
        }}
        
        .sidebar-name {{
            font-size: 1.5rem;
        }}
        
        .main-section-title {{
            font-size: 1.2rem;
        }}
    }}

    /* Print Styles */
    @media print {{
        body {{
            background: #ffffff;
            padding: 0;
        }}
        
        .resume-container {{
            max-width: none;
            padding: 0;
        }}
        
        .resume-main-container {{
            box-shadow: none;
            border-radius: 0;
            min-height: auto;
        }}
        
        .main-exp-item {{
            page-break-inside: avoid;
        }}
        
        .sidebar-section {{
            page-break-inside: avoid;
        }}
    }}
    '''
    return css