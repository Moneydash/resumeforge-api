from flask import Blueprint, request, jsonify, send_file, current_app
from weasyprint import HTML, CSS
import os
import tempfile
import uuid
from datetime import datetime
import logging
from utils.helper import format_date, format_description, calcHeightModern1, export_pdf_response

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_pdf():
    """Generate a creative, professional PDF resume (Milky Way template)"""
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
            stylesheets=[CSS(string=get_creative_css(dynamic_height))]
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
        css_content = get_creative_css(dynamic_height)
        return export_pdf_response(html_content, css_content)
    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def generate_resume_html(resume_data):
    """Generate HTML for creative/professional resume"""
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{resume_data.get('personal', {}).get('name', 'Resume')}</title>
    </head>
    <body>
        <div class="mw-container">
            <header class="mw-header">
                <div class="mw-header-bg"></div>
                <h1 class="mw-name">{resume_data.get('personal', {}).get('name', '')}</h1>
                <h2 class="mw-headline">{resume_data.get('personal', {}).get('headline', '')}</h2>
                <div class="mw-contact">
                    {f'<span>{resume_data.get("personal", {}).get("email", "")}</span>' if resume_data.get('personal', {}).get('email') else ''}
                    {f'<span>{resume_data.get("personal", {}).get("location", "")}</span>' if resume_data.get('personal', {}).get('location') else ''}
                    {f'<span><a href="{resume_data.get("personal", {}).get("website", {}).get("link", "")}">{resume_data.get("personal", {}).get("website", {}).get("name", "") or resume_data.get("personal", {}).get("website", {}).get("link", "")}</a></span>' if resume_data.get('personal', {}).get('website', {}).get('link') else ''}
                </div>
            </header>
            <main class="mw-main">
                {f'<section class="mw-section"><h2 class="mw-section-title">About Me</h2><div class="mw-summary">{format_description(resume_data.get("summary", ""))}</div></section>' if resume_data.get('summary') else ''}
                {f'<section class="mw-section"><h2 class="mw-section-title">Work Experience</h2>' if resume_data.get('experience') else ''}
                {''.join([
                    f'''<div class="mw-item mw-card">
                        <div class="mw-item-header">
                            <span class="mw-item-title">{job.get('title', '')}</span> <span class="mw-item-company">@ {job.get('company', '')}</span>
                            <span class="mw-item-date">{format_date(job.get('startDate', ''))} - {format_date(job.get('endDate', '')) if job.get('endDate') else 'Present'}</span>
                        </div>
                        <div class="mw-item-description">{format_description(job.get('description', ''))}</div>
                    </div>''' for job in resume_data.get('experience', [])])}
                {f'</section>' if resume_data.get('experience') else ''}
                {f'<section class="mw-section"><h2 class="mw-section-title">Education</h2>' if resume_data.get('education') else ''}
                {''.join([
                    f'''<div class="mw-item mw-card">
                        <div class="mw-item-header">
                            <span class="mw-item-title">{edu.get('degree', '')}</span> <span class="mw-item-company">@ {edu.get('institution', '')}</span>
                            <span class="mw-item-date">{format_date(edu.get('startDate', ''))} - {format_date(edu.get('endDate', '')) if edu.get('endDate') else 'Present'}</span>
                        </div>
                        <div class="mw-item-description">{format_description(edu.get('description', ''))}</div>
                    </div>''' for edu in resume_data.get('education', [])])}
                {f'</section>' if resume_data.get('education') else ''}
                {f'<section class="mw-section"><h2 class="mw-section-title">Projects</h2>' if resume_data.get('projects') else ''}
                {''.join([
                    f'''<div class="mw-item mw-card">
                        <div class="mw-item-header">
                            <span class="mw-item-title">{project.get('title', '')}</span>
                            <span class="mw-item-tech">{', '.join(project.get('technologies', []))}</span>
                        </div>
                        <div class="mw-item-description">{format_description(project.get('description', ''))}</div>
                    </div>''' for project in resume_data.get('projects', [])])}
                {f'</section>' if resume_data.get('projects') else ''}
                {f'<section class="mw-section"><h2 class="mw-section-title">Skills</h2><div class="mw-skills">' + ' '.join([f'<span class="mw-skill-pill">{skill}</span>' for skill in resume_data.get('skills', {}).get('keywords', [])]) + '</div></section>' if resume_data.get('skills', {}).get('keywords') else ''}
                {f'<section class="mw-section"><h2 class="mw-section-title">Languages</h2><div class="mw-languages">' + ', '.join(resume_data.get('languages', [])) + '</div></section>' if resume_data.get('languages') else ''}
                {f'<section class="mw-section"><h2 class="mw-section-title">Certifications</h2>' if resume_data.get('certifications') else ''}
                {''.join([
                    f'''<div class="mw-item mw-card">
                        <div class="mw-item-header">
                            <span class="mw-item-title">{cert.get('name', '')}</span> <span class="mw-item-company">@ {cert.get('issuingOrganization', '')}</span>
                            <span class="mw-item-date">{format_date(cert.get('date', ''))}</span>
                        </div>
                    </div>''' for cert in resume_data.get('certifications', [])])}
                {f'</section>' if resume_data.get('certifications') else ''}
                {f'<section class="mw-section"><h2 class="mw-section-title">Awards</h2>' if resume_data.get('awards') else ''}
                {''.join([
                    f'''<div class="mw-item mw-card">
                        <div class="mw-item-header">
                            <span class="mw-item-title">{award.get('title', '')}</span> <span class="mw-item-company">@ {award.get('awarder', '')}</span>
                            <span class="mw-item-date">{format_date(award.get('date', ''))}</span>
                        </div>
                        <div class="mw-item-description">{format_description(award.get('summary', ''))}</div>
                    </div>''' for award in resume_data.get('awards', [])])}
                {f'</section>' if resume_data.get('awards') else ''}
                {f'<section class="mw-section"><h2 class="mw-section-title">Interests</h2><div class="mw-interests">' + ', '.join(resume_data.get('interests', [])) + '</div></section>' if resume_data.get('interests') else ''}
                {f'<section class="mw-section"><h2 class="mw-section-title">References</h2>' if resume_data.get('references') else ''}
                {''.join([
                    f'''<div class="mw-item mw-card">
                        <div class="mw-item-header">
                            <span class="mw-item-title">{ref.get('name', '')}</span> <span class="mw-item-company">@ {ref.get('relationship', '')}</span>
                        </div>
                        <div class="mw-item-description">{format_description(ref.get('contact', ''))}</div>
                    </div>''' for ref in resume_data.get('references', [])])}
                {f'</section>' if resume_data.get('references') else ''}
            </main>
        </div>
    </body>
    </html>
    '''
    return html

def get_creative_css(dynamic_height):
    """Return CSS for a creative, professional resume"""
    dynamic_height -= 400
    css = f"""
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Lato:wght@400;700&display=swap');
    @page {{
        margin: 0;
        size: 612pt {dynamic_height}pt;
    }}
    """

    css += """
    body {
        font-family: 'Lato', Arial, Helvetica, sans-serif;
        color: #232323;
        margin: 0;
        padding: 0;
    }
    .mw-container {
        margin: 0 auto;
        background: #fff;
        box-shadow: 0 4px 24px rgba(80,0,160,0.08);
        overflow: hidden;
    }
    .mw-header {
        position: relative;
        background: linear-gradient(100deg, #7b2ff2 0%, #f357a8 100%);
        color: #fff;
        text-align: center;
        padding: 2.4rem 1.5rem 1.7rem 1.5rem;
        border-bottom-left-radius: 32px 10px;
        border-bottom-right-radius: 32px 10px;
        box-shadow: 0 2px 10px rgba(123,47,242,0.08);
    }
    .mw-header-bg {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: url('https://svgshare.com/i/13wC.svg') repeat-x bottom;
        opacity: 0.08;
        z-index: 1;
    }
    .mw-name {
        font-family: 'Poppins', Arial, sans-serif;
        font-size: 2.4rem;
        font-weight: 700;
        margin: 0;
        position: relative;
        z-index: 2;
        letter-spacing: 1px;
    }
    .mw-headline {
        font-family: 'Poppins', Arial, sans-serif;
        font-size: 1.18rem;
        font-weight: 600;
        margin: 0.5rem 0 0.8rem 0;
        opacity: 0.92;
        position: relative;
        z-index: 2;
    }
    .mw-contact {
        font-size: 0.98rem;
        margin-top: 0.5rem;
        color: #f3e7ff;
        display: flex;
        gap: 1.4rem;
        justify-content: center;
        flex-wrap: wrap;
        position: relative;
        z-index: 2;
    }
    .mw-contact a {
        color: #fff;
        text-decoration: underline dotted;
    }
    .mw-main {
        padding: 2.2rem 2.5rem 2.5rem 2.5rem;
    }
    .mw-section {
        margin-bottom: 1.7rem;
    }
    .mw-section-title {
        font-family: 'Poppins', Arial, sans-serif;
        font-size: 1.12rem;
        font-weight: 700;
        color: #7b2ff2;
        margin-bottom: 0.7rem;
        letter-spacing: 0.7px;
        border-left: 5px solid #f357a8;
        padding-left: 0.75rem;
        background: linear-gradient(90deg, #f3e7ff 0%, #fff 100%);
        border-radius: 6px 0 0 6px;
        display: inline-block;
        box-shadow: 0 1px 4px rgba(243,87,168,0.04);
    }
    .mw-item {
        margin-bottom: 1.2rem;
    }
    .mw-card {
        background: #f8f9fa;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(123,47,242,0.06);
        padding: 1.1rem 1.3rem 0.9rem 1.3rem;
        border-left: 4px solid #7b2ff2;
    }
    .mw-item-header {
        font-size: 1.04rem;
        font-family: 'Poppins', Arial, sans-serif;
        font-weight: 600;
        color: #232323;
        margin-bottom: 0.18rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        align-items: baseline;
    }
    .mw-item-title {
        font-weight: 700;
    }
    .mw-item-company {
        font-weight: 500;
        color: #7b2ff2;
        margin-left: 0.5rem;
    }
    .mw-item-date {
        margin-left: auto;
        font-size: 0.97rem;
        color: #f357a8;
        font-family: 'Lato', Arial, Helvetica, sans-serif;
    }
    .mw-item-description {
        font-size: 0.97rem;
        color: #232323;
        margin-left: 0.1rem;
        margin-top: 0.18rem;
        line-height: 1.6;
        text-align: justify;
    }
    .mw-skills, .mw-languages, .mw-interests {
        font-size: 0.98rem;
        color: #232323;
        margin-left: 0.1rem;
        margin-bottom: 0.2rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .mw-skill-pill {
        background: linear-gradient(90deg, #f357a8 0%, #7b2ff2 100%);
        color: #fff;
        padding: 0.27rem 0.95rem;
        border-radius: 50px;
        font-size: 0.92rem;
        font-family: 'Poppins', Arial, sans-serif;
        font-weight: 600;
        margin-bottom: 0.2rem;
        box-shadow: 0 1px 3px rgba(123,47,242,0.09);
        letter-spacing: 0.2px;
    }
    .mw-item-tech {
        font-size: 0.95rem;
        color: #f357a8;
        margin-left: 0.6rem;
        font-family: 'Poppins', Arial, sans-serif;
    }
    """
    return css
