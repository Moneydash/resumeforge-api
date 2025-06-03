from flask import Blueprint, request, jsonify, send_file, current_app
from weasyprint import HTML, CSS
import os
import tempfile
import uuid
from datetime import datetime
import logging
from utils.helper import calcHeightModern1, format_date, format_description, export_pdf_response

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_pdf():
    """Generate a PDF resume from the provided data and return it as a preview (classic-modern style)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No resume data provided'}), 400
        temp_dir = tempfile.gettempdir()
        filename = f"resume_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(temp_dir, filename)
        html_content = generate_resume_html(data)
        dynamic_height = calcHeightModern1(data)
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string=get_classic_css(dynamic_height))]
        )
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
        css_content = get_classic_css(dynamic_height)
        return export_pdf_response(html_content, css_content)
    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def generate_resume_html(resume_data):
    """Generate HTML content for the classic-modern resume template"""
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{resume_data.get('personal', {}).get('name', 'Resume')}</title>
    </head>
    <body>
        <div class="resume-classic-container">
            <header class="classic-header">
                <h1 class="classic-name">{resume_data.get('personal', {}).get('name', '')}</h1>
                <h2 class="classic-headline">{resume_data.get('personal', {}).get('headline', '')}</h2>
                <div class="classic-contact">
                    {f'<span>{resume_data.get("personal", {}).get("email", "")}</span>' if resume_data.get('personal', {}).get('email') else ''}
                    {f'<span>{resume_data.get("personal", {}).get("location", "")}</span>' if resume_data.get('personal', {}).get('location') else ''}
                    {f'<span><a href="{resume_data.get("personal", {}).get("website", {}).get("link", "")}">{resume_data.get("personal", {}).get("website", {}).get("name", "") or resume_data.get("personal", {}).get("website", {}).get("link", "")}</a></span>' if resume_data.get('personal', {}).get('website', {}).get('link') else ''}
                </div>
                <div class="classic-socials">
                    {f'<a href="https://linkedin.com/in/{resume_data.get("socials", {}).get("linkedIn", "").strip("https://linkedin.com/in/")}">LinkedIn</a>' if resume_data.get('socials', {}).get('linkedIn') else ''}
                    {f'<a href="https://github.com/{resume_data.get("socials", {}).get("github", "").strip("https://github.com/")}">GitHub</a>' if resume_data.get('socials', {}).get('github') else ''}
                    {f'<a href="https://twitter.com/{resume_data.get("socials", {}).get("twitter", "").strip("https://twitter.com/")}">Twitter</a>' if resume_data.get('socials', {}).get('twitter') else ''}
                </div>
            </header>
            <main class="classic-main">
                {f'<section class="classic-section"><h2 class="classic-section-title">About Me</h2><div class="classic-summary">{format_description(resume_data.get("summary", ""))}</div></section>' if resume_data.get('summary') else ''}
                {f'<section class="classic-section"><h2 class="classic-section-title">Work Experience</h2>' if resume_data.get('experience') else ''}
                {''.join([
                    f'''<div class="classic-item">
                        <div class="classic-item-header">
                            <span class="classic-item-title">{job.get('title', '')}</span> | <span class="classic-item-subtitle">{job.get('company', '')}</span>
                            <span class="classic-item-date">{format_date(job.get('startDate', ''))} - {format_date(job.get('endDate', '')) if job.get('endDate') else 'Present'}</span>
                        </div>
                        <div class="classic-item-description">{format_description(job.get('description', ''))}</div>
                    </div>''' for job in resume_data.get('experience', [])])}
                {f'</section>' if resume_data.get('experience') else ''}
                {f'<section class="classic-section"><h2 class="classic-section-title">Education</h2>' if resume_data.get('education') else ''}
                {''.join([
                    f'''<div class="classic-item">
                        <div class="classic-item-header">
                            <span class="classic-item-title">{edu.get('degree', '')}</span> | <span class="classic-item-subtitle">{edu.get('institution', '')}</span>
                            <span class="classic-item-date">{format_date(edu.get('startDate', ''))} - {format_date(edu.get('endDate', '')) if edu.get('endDate') else 'Present'}</span>
                        </div>
                        <div class="classic-item-description">{format_description(edu.get('description', ''))}</div>
                    </div>''' for edu in resume_data.get('education', [])])}
                {f'</section>' if resume_data.get('education') else ''}
                {f'<section class="classic-section"><h2 class="classic-section-title">Projects</h2>' if resume_data.get('projects') else ''}
                {''.join([
                    f'''<div class="classic-item">
                        <div class="classic-item-header">
                            <span class="classic-item-title">{project.get('title', '')}</span>
                            <span class="classic-item-date">{', '.join(project.get('technologies', []))}</span>
                        </div>
                        <div class="classic-item-description">{format_description(project.get('description', ''))}</div>
                    </div>''' for project in resume_data.get('projects', [])])}
                {f'</section>' if resume_data.get('projects') else ''}
                {f'<section class="classic-section"><h2 class="classic-section-title">Skills</h2><div class="classic-skills">' + ', '.join(resume_data.get('skills', {}).get('keywords', [])) + '</div></section>' if resume_data.get('skills', {}).get('keywords') else ''}
                {f'<section class="classic-section"><h2 class="classic-section-title">Languages</h2><div class="classic-languages">' + ', '.join(resume_data.get('languages', [])) + '</div></section>' if resume_data.get('languages') else ''}
                {f'<section class="classic-section"><h2 class="classic-section-title">Certifications</h2>' if resume_data.get('certifications') else ''}
                {''.join([
                    f'''<div class="classic-item">
                        <div class="classic-item-header">
                            <span class="classic-item-title">{cert.get('name', '')}</span> | <span class="classic-item-subtitle">{cert.get('issuingOrganization', '')}</span>
                            <span class="classic-item-date">{format_date(cert.get('date', ''))}</span>
                        </div>
                    </div>''' for cert in resume_data.get('certifications', [])])}
                {f'</section>' if resume_data.get('certifications') else ''}
                {f'<section class="classic-section"><h2 class="classic-section-title">Awards</h2>' if resume_data.get('awards') else ''}
                {''.join([
                    f'''<div class="classic-item">
                        <div class="classic-item-header">
                            <span class="classic-item-title">{award.get('title', '')}</span> | <span class="classic-item-subtitle">{award.get('awarder', '')}</span>
                            <span class="classic-item-date">{format_date(award.get('date', ''))}</span>
                        </div>
                        <div class="classic-item-description">{format_description(award.get('summary', ''))}</div>
                    </div>''' for award in resume_data.get('awards', [])])}
                {f'</section>' if resume_data.get('awards') else ''}
                {f'<section class="classic-section"><h2 class="classic-section-title">References</h2>' if resume_data.get('references') else ''}
                {''.join([
                    f'''<div class="classic-item">
                        <div class="classic-item-header">
                            <span class="classic-item-title">{ref.get('name', '')}</span> | <span class="classic-item-subtitle">{ref.get('relationship', '')}</span>
                        </div>
                        <div class="classic-item-description">{format_description(ref.get('contact', ''))}</div>
                    </div>''' for ref in resume_data.get('references', [])])}
                {f'</section>' if resume_data.get('references') else ''}
            </main>
        </div>
    </body>
    </html>
    '''
    return html

def get_classic_css(dynamic_height):
    """Return CSS for a classic-modern resume template"""
    dynamic_height -= 850
    css = f'''
    @import url('https://fonts.googleapis.com/css2?family=Georgia:wght@400;700&family=Montserrat:wght@500;700&display=swap');
    @page {{
        margin: 0;
        size: 612pt {dynamic_height}pt;
    }}
    body {{
        font-family: 'Georgia', Times, 'Times New Roman', serif;
        color: #232323;
        background: #fff;
        margin: 0;
        padding: 0;
    }}
    .resume-classic-container {{
        background: #fff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin: 1rem;
    }}
    .classic-header {{
        text-align: center;
        border-bottom: 2px solid #1a237e;
        padding-bottom: 0.8rem;
        margin-bottom: 1.5rem;
    }}
    .classic-name {{
        font-family: 'Montserrat', Arial, sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a237e;
        margin: 0;
    }}
    .classic-headline {{
        font-family: 'Montserrat', Arial, sans-serif;
        font-size: 1.15rem;
        font-weight: 500;
        color: #232323;
        margin: 0.35rem 0 0.7rem 0;
    }}
    .classic-contact {{
        font-size: 0.97rem;
        color: #444;
        margin-bottom: 0.3rem;
        display: flex;
        gap: 1.5rem;
        justify-content: center;
        flex-wrap: wrap;
    }}
    .classic-contact a {{
        color: #1a237e;
        text-decoration: none;
    }}
    .classic-socials {{
        margin-top: 0.2rem;
        font-size: 0.95rem;
        display: flex;
        gap: 1.1rem;
        justify-content: center;
        flex-wrap: wrap;
    }}
    .classic-socials a {{
        color: #1a237e;
        text-decoration: none;
        font-weight: 500;
    }}
    .classic-main {{
        margin-top: 1.7rem;
    }}
    .classic-section {{
        margin-bottom: 1.45rem;
    }}
    .classic-section-title {{
        font-family: 'Montserrat', Arial, sans-serif;
        font-size: 1.08rem;
        font-weight: 700;
        color: #1a237e;
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 0.13rem;
    }}
    .classic-item {{
        margin-bottom: 1.1rem;
    }}
    .classic-item-header {{
        font-size: 1.01rem;
        font-family: 'Montserrat', Arial, sans-serif;
        font-weight: 500;
        color: #232323;
        margin-bottom: 0.15rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        align-items: baseline;
    }}
    .classic-item-title {{
        font-weight: 700;
    }}
    .classic-item-subtitle {{
        color: #444;
    }}
    .classic-item-date {{
        margin-left: auto;
        font-size: 0.97rem;
        color: #555;
        font-family: 'Georgia', Times, 'Times New Roman', serif;
    }}
    .classic-item-description {{
        font-size: 0.97rem;
        color: #232323;
        margin-left: 0.1rem;
        margin-top: 0.18rem;
        line-height: 1.6;
        text-align: justify;
    }}
    .classic-skills, .classic-languages {{
        font-size: 0.97rem;
        color: #232323;
        margin-left: 0.1rem;
        margin-bottom: 0.2rem;
    }}
    '''
    return css
