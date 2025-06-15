# zeus
import os
from flask import redirect, request, jsonify, current_app
import logging
from utils.zeus_helper import buff_calc
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
        cached_pdf = data_caching(data, "zeus")
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
        increment = increment_calc(data, 20)
        final_css = css_height_calc(html_content, get_zeus_css, data.get('personal', {}).get('email'), 'zeus', buffer, max_attempts, increment)
        pdf_path = upload_pdf_to_supabase(name, "zeus", html_content, final_css)

        combined_data = {
            "template": "zeus",
            "resume_data": data
        }

        # Cache new data and PDF path
        redis_client = current_app.redis_client
        data_str = json.dumps(combined_data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        redis_client.set(f"{data['personal']['email']}_data_hash_zeus", data_hash)
        redis_client.set(f"{data['personal']['email']}_storage_path_zeus", pdf_path)

        supabase = current_app.supabase
        url_res = supabase.storage.from_(supabase_bucket_name).get_public_url(pdf_path)
        return redirect(url_res)

    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def generate_resume_html(resume_data):
    """Generate HTML content for the Greek Zeus-themed resume template"""
    # About Me
    about_html = ''
    if resume_data.get('summary'):
        about_html = f'<section class="greek-section"><h2 class="greek-section-title"><span class="greek-icon">⚡</span>About Me</h2><div class="greek-summary">{format_description(resume_data.get("summary", ""))}</div></section>'

    # Work Experience
    experience_html = ''
    if resume_data.get('experience'):
        experience_html += '<section class="greek-section"><h2 class="greek-section-title"><span class="greek-icon">🏛️</span>Work Experience</h2>'
        for job in resume_data.get('experience', []):
            experience_html += f'''
                <div class="greek-item">
                    <div class="greek-item-header">
                        <span class="greek-item-title">{job.get('title', '')}</span>
                        <span class="greek-item-date">{format_date(job.get('startDate', ''))} - {format_date(job.get('endDate', '')) if job.get('endDate') else 'Present'}</span>
                    </div>
                    <span class="greek-item-subtitle">{job.get('company', '')}</span>
                    <div class="greek-item-description">{format_description(job.get('description', ''))}</div>
                </div>'''
        experience_html += '</section>'

    # Education
    education_html = ''
    if resume_data.get('education'):
        education_html += '<section class="greek-section"><h2 class="greek-section-title"><span class="greek-icon">🎓</span>Education</h2>'
        for edu in resume_data.get('education', []):
            education_html += f'''
                <div class="greek-item">
                    <div class="greek-item-header">
                        <span class="greek-item-title">{edu.get('degree', '')}</span>
                        <span class="greek-item-date">{format_date(edu.get('startDate', ''))} - {format_date(edu.get('endDate', '')) if edu.get('endDate') else 'Present'}</span>
                    </div>
                    <span class="greek-item-subtitle">{edu.get('institution', '')}</span>
                </div>'''
        education_html += '</section>'

    # Projects
    projects_html = ''
    if resume_data.get('projects'):
        projects_html += '<section class="greek-section"><h2 class="greek-section-title"><span class="greek-icon">⚔️</span>Projects</h2>'
        for project in resume_data.get('projects', []):
            projects_html += f'''
                <div class="greek-item">
                    <div class="greek-item-header">
                        <span class="greek-item-title">{project.get('title', '')}</span>
                        <span class="greek-item-date">{', '.join(project.get('technologies', []))}</span>
                    </div>
                    <div class="greek-item-description">{format_description(project.get('description', ''))}</div>
                </div>'''
        projects_html += '</section>'

    # Skills
    all_keywords = []
    for skill in resume_data.get('skills', []):
        all_keywords.extend(skill.get('keywords', []))

    skills_html = (
        '<section class="greek-section"><h2 class="greek-section-title"><span class="greek-icon">🔱</span>Skills</h2>'
        '<div class="greek-skills">' + ' • '.join(all_keywords) + '</div></section>'
    )

    # Languages
    languages_html = ''
    if resume_data.get('languages'):
        languages_html = f'<section class="greek-section"><h2 class="greek-section-title"><span class="greek-icon">🗣️</span>Languages</h2><div class="greek-languages">' + ' • '.join(resume_data.get('languages', [])) + '</div></section>'

    # Certifications
    certifications_html = ''
    if resume_data.get('certifications'):
        certifications_html += '<section class="greek-section"><h2 class="greek-section-title"><span class="greek-icon">🏆</span>Certifications</h2>'
        for cert in resume_data.get('certifications', []):
            certifications_html += f'''
                <div class="greek-item">
                    <div class="greek-item-header">
                        <span class="greek-item-title">{cert.get('name', '')}</span> | <span class="greek-item-subtitle">{cert.get('issuingOrganization', '')}</span>
                        <span class="greek-item-date">{format_date(cert.get('date', ''))}</span>
                    </div>
                </div>'''
        certifications_html += '</section>'

    # Awards
    awards_html = ''
    if resume_data.get('awards'):
        awards_html += '<section class="greek-section"><h2 class="greek-section-title"><span class="greek-icon">👑</span>Awards</h2>'
        for award in resume_data.get('awards', []):
            awards_html += f'''
                <div class="greek-item">
                    <div class="greek-item-header">
                        <span class="greek-item-title">{award.get('title', '')}</span>
                        <span class="greek-item-date">{format_date(award.get('date', ''))}</span>
                    </div>
                    <div class="greek-item-description">{format_description(award.get('summary', ''))}</div>
                </div>'''
        awards_html += '</section>'

    # References
    references_html = ''
    if resume_data.get('references'):
        references_html += '<section class="greek-section"><h2 class="greek-section-title"><span class="greek-icon">🤝</span>References</h2>'
        for ref in resume_data.get('references', []):
            references_html += f"""
                <div class="greek-item">
                    <div class="greek-item-header">
                        <span class="greek-item-title">{ref.get("name", "")}</span> | <span class="greek-item-subtitle">{ref.get("company", "")}</span>
                    </div>
                    <div class="greek-item-description">{format_description(ref.get('contact', ''))}</div>
                </div>"""
        references_html += '</section>'

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
        <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Text:ital@0;1&display=swap" rel="stylesheet">
    </head>
    <body>
        <div class="resume-greek-container">
            <div class="greek-border-top"></div>
            <header class="greek-header">
                <div class="greek-laurel-left">🏛️</div>
                <div class="greek-header-content">
                    <h1 class="greek-name">{resume_data.get('personal', {}).get('name', '')}</h1>
                    <h2 class="greek-headline">{resume_data.get('personal', {}).get('headline', '')}</h2>
                    <div class="greek-contact">
                        {f'<span>📧 {resume_data.get("personal", {}).get("email", "")}</span>' if resume_data.get('personal', {}).get('email') else ''}
                        {f'<span>📍 {resume_data.get("personal", {}).get("location", "")}</span>' if resume_data.get('personal', {}).get('location') else ''}
                        {f'<span>🌐 <a href="{resume_data.get("personal", {}).get("website", {}).get("link", "")}">{resume_data.get("personal", {}).get("website", {}).get("name", "") or resume_data.get("personal", {}).get("website", {}).get("link", "")}</a></span>' if resume_data.get('personal', {}).get('website', {}).get('link') else ''}
                    </div>
                    <div class="greek-socials">
                '''

    for social in resume_data.get('socials', []):
        html += f'''
            {f'<a href="{social.get("link")}"><i class="fab fa-{social.get("slug")} fa-lg"></i></a>' if social.get('link') else ''}
        '''

    html += f'''
                    </div>
                </div>
                <div class="greek-laurel-right">⚡</div>
            </header>
            <main class="greek-main">
                {about_html}
                {experience_html}
                {education_html}
                {projects_html}
                {skills_html}
                {languages_html}
                {certifications_html}
                {awards_html}
                {references_html}
            </main>
        </div>
    </body>
    </html>
    '''
    return html

def get_zeus_css(dynamic_height=None):
    height = f"{dynamic_height}pt" if dynamic_height else "1009pt"
    css = f'''
    @page {{
        margin: 0;
        size: 612pt {height};
    }}
    * {{
        box-sizing: border-box;
    }}
    body {{
        font-family: 'DM Serif Text', Georgia, serif;
        color: #2c1810;
        background: linear-gradient(135deg, #f5f1e8 0%, #ede4d1 100%);
        margin: 0;
        padding: 0;
    }}
    .resume-greek-container {{
        background: linear-gradient(135deg, #faf7f0 0%, #f0ead6 100%);
        box-shadow: 0 8px 32px rgba(0,0,0,0.15), inset 0 2px 4px rgba(255,215,0,0.2);
        margin: 0;
        position: relative;
        overflow: hidden;
    }}
    .greek-border-top {{
        height: 8px;
        background: linear-gradient(90deg, #d4af37 0%, #ffd700 25%, #b8860b 50%, #ffd700 75%, #d4af37 100%);
        background-size: 40px 8px;
        animation: shimmer 3s linear infinite;
    }}
    @keyframes shimmer {{
        0% {{ background-position: -40px 0; }}
        100% {{ background-position: 40px 0; }}
    }}
    .greek-header {{
        text-align: center;
        background: linear-gradient(135deg, #1a2855 0%, #2d4a9a 50%, #1a2855 100%);
        color: #ffd700;
        padding: 1.5rem 2rem;
        position: relative;
        border-bottom: 4px solid #d4af37;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .greek-header::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M0 0h100v100H0z" fill="none"/><path d="M10 10l80 80M90 10L10 90" stroke="%23ffd700" stroke-width="0.5" opacity="0.1"/></svg>');
        pointer-events: none;
    }}
    .greek-laurel-left, .greek-laurel-right {{
        font-size: 2rem;
        color: #ffd700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    .greek-header-content {{
        flex: 1;
        z-index: 1;
    }}
    .greek-name {{
        font-family: 'Cinzel', serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffd700;
        margin: 0;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.4);
        letter-spacing: 2px;
        text-transform: uppercase;
    }}
    .greek-headline {{
        font-family: 'Cinzel', serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: #e6d7b8;
        margin: 0.5rem 0 1rem 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        font-style: italic;
    }}
    .greek-contact {{
        font-size: 1rem;
        color: #f0e6d2;
        margin-bottom: 0.8rem;
        display: flex;
        gap: 2rem;
        justify-content: center;
        flex-wrap: wrap;
    }}
    .greek-contact a {{
        color: #ffd700;
        text-decoration: none;
        font-weight: 600;
    }}
    .greek-contact a:hover {{
        text-shadow: 0 0 8px rgba(255,215,0,0.6);
    }}
    .greek-socials {{
        margin-top: 0.8rem;
        display: flex;
        gap: 1.5rem;
        justify-content: center;
        flex-wrap: wrap;
    }}
    .greek-socials a {{
        color: #ffd700;
        text-decoration: none;
        font-size: 1.2rem;
        transition: all 0.3s ease;
    }}
    .greek-socials a:hover {{
        color: #fff;
        text-shadow: 0 0 12px rgba(255,215,0,0.8);
        transform: scale(1.2);
    }}
    .greek-main {{
        padding: 1.5rem 2rem;
        background: linear-gradient(135deg, #faf7f0 0%, #f0ead6 100%);
    }}
    .greek-section {{
        margin-bottom: 2rem;
        background: rgba(255,255,255,0.7);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-left: 6px solid #d4af37;
        position: relative;
    }}
    .greek-section::before {{
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 30px;
        height: 100%;
        background: linear-gradient(180deg, transparent 0%, rgba(212,175,55,0.1) 50%, transparent 100%);
        pointer-events: none;
    }}
    .greek-section-title {{
        font-family: 'Cinzel', serif;
        font-size: 1.4rem;
        font-weight: 700;
        color: #1a2855;
        margin-bottom: 1rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        border-bottom: 2px solid #d4af37;
        padding-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }}
    .greek-icon {{
        font-size: 1.2rem;
        color: #d4af37;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }}
    .greek-item {{
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: rgba(255,255,255,0.5);
        border-radius: 6px;
        border-left: 3px solid #b8860b;
    }}
    .greek-item-header {{
        font-size: 1.1rem;
        font-family: 'Cinzel', serif;
        font-weight: 600;
        color: #1a2855;
        margin-bottom: 0.3rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.8rem;
        align-items: baseline;
    }}
    .greek-item-title {{
        font-weight: 700;
        color: #2d4a9a;
    }}
    .greek-item-subtitle {{
        color: #8b4513;
        font-style: italic;
    }}
    .greek-item-date {{
        margin-left: auto;
        font-size: 1rem;
        color: #b8860b;
        font-family: 'DM Serif Text', serif;
        font-weight: 600;
    }}
    .greek-item-description {{
        font-size: 1rem;
        color: #2c1810;
        margin-left: 0.2rem;
        margin-top: 0.5rem;
        line-height: 1.7;
        text-align: justify;
    }}
    .greek-skills, .greek-languages {{
        font-size: 1rem;
        color: #2c1810;
        margin-left: 0.2rem;
        margin-bottom: 0.5rem;
        line-height: 1.8;
        font-weight: 600;
    }}
    ul.list-disc.ml-3,
    ul.ml-3 {{
        margin-left: 0 !important;
        padding-left: 1.2em;
    }}
    ul.list-disc {{
        list-style-type: none;
    }}
    ul.list-disc li {{
        margin-top: 0;
        margin-bottom: 0.6em;
        position: relative;
        padding-left: 1.5em;
    }}
    ul.list-disc li::before {{
        content: '⚡';
        position: absolute;
        left: 0;
        color: #d4af37;
        font-size: 0.9em;
    }}
    ul.list-disc li:not(:first-child) {{
        margin-top: -2px;
    }}
    ul.list-disc li p {{
        margin: 0;
        padding: 0;
    }}
    '''
    return css