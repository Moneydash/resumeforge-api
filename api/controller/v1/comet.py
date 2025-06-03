from flask import Blueprint, request, jsonify, send_file, current_app
from weasyprint import HTML, CSS
import os
import tempfile
import uuid
from datetime import datetime
import logging
from utils.helper import format_description, export_pdf_response

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_pdf():
    """Generate a minimal PDF resume for new grads/interns (summary, skills, projects, interests only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No resume data provided'}), 400
        temp_dir = tempfile.gettempdir()
        filename = f"resume_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(temp_dir, filename)
        html_content = generate_resume_html(data)
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string=get_minimal_css())]
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
        css_content = get_minimal_css()
        return export_pdf_response(html_content, css_content)
    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

def generate_resume_html(resume_data):
    """Generate HTML for minimal resume (summary, skills, projects, interests)"""
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{resume_data.get('personal', {}).get('name', 'Resume')}</title>
    </head>
    <body>
        <div class="comet-container">
            <header class="comet-header">
                <h1 class="comet-name">{resume_data.get('personal', {}).get('name', '')}</h1>
                <h2 class="comet-headline">{resume_data.get('personal', {}).get('headline', '')}</h2>
                <div class="comet-contact">
                    {f'<span>{resume_data.get("personal", {}).get("email", "")}</span>' if resume_data.get('personal', {}).get('email') else ''}
                    {f'<span>{resume_data.get("personal", {}).get("location", "")}</span>' if resume_data.get('personal', {}).get('location') else ''}
                    {f'<span><a href="{resume_data.get("personal", {}).get("website", {}).get("link", "")}">{resume_data.get("personal", {}).get("website", {}).get("name", "") or resume_data.get("personal", {}).get("website", {}).get("link", "")}</a></span>' if resume_data.get('personal', {}).get('website', {}).get('link') else ''}
                </div>
            </header>
            <main class="comet-main">
                {f'<section class="comet-section"><h2 class="comet-section-title">About Me</h2><div class="comet-summary">{format_description(resume_data.get("summary", ""))}</div></section>' if resume_data.get('summary') else ''}
                {f'<section class="comet-section"><h2 class="comet-section-title">Skills</h2><div class="comet-skills">' + ', '.join(resume_data.get('skills', {}).get('keywords', [])) + '</div></section>' if resume_data.get('skills', {}).get('keywords') else ''}
                {f'<section class="comet-section"><h2 class="comet-section-title">Projects</h2>' if resume_data.get('projects') else ''}
                {''.join([
                    f'''<div class="comet-item">
                        <div class="comet-item-header">
                            <span class="comet-item-title">{project.get('title', '')}</span>
                            <span class="comet-item-tech">{', '.join(project.get('technologies', []))}</span>
                        </div>
                        <div class="comet-item-description">{format_description(project.get('description', ''))}</div>
                    </div>''' for project in resume_data.get('projects', [])])}
                {f'</section>' if resume_data.get('projects') else ''}
                {f'<section class="comet-section"><h2 class="comet-section-title">Interests</h2><div class="comet-interests">' + ', '.join(resume_data.get('interests', [])) + '</div></section>' if resume_data.get('interests') else ''}
            </main>
        </div>
    </body>
    </html>
    '''
    return html

def get_minimal_css():
    """Return CSS for a minimal, clean resume"""
    css = f'''
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    @page {{
        margin: 0;
        size: letter;
    }}
    body {{
        font-family: 'Inter', Arial, Helvetica, sans-serif;
        color: #232323;
        background: #fff;
        margin: 0;
        padding: 0;
    }}
    .comet-container {{
        margin: 0 auto;
        background: #fff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        padding: 2.2rem 2.2rem 2.2rem 2.2rem;
    }}
    .comet-header {{
        text-align: center;
        border-bottom: 2px solid #1976d2;
        padding-bottom: 0.7rem;
        margin-bottom: 1.3rem;
    }}
    .comet-name {{
        font-size: 2.1rem;
        font-weight: 700;
        color: #1976d2;
        margin: 0;
    }}
    .comet-headline {{
        font-size: 1.1rem;
        font-weight: 500;
        color: #232323;
        margin: 0.3rem 0 0.7rem 0;
    }}
    .comet-contact {{
        font-size: 0.97rem;
        color: #444;
        margin-bottom: 0.3rem;
        display: flex;
        gap: 1.2rem;
        justify-content: center;
        flex-wrap: wrap;
    }}
    .comet-contact a {{
        color: #1976d2;
        text-decoration: none;
    }}
    .comet-main {{
        margin-top: 1.2rem;
    }}
    .comet-section {{
        margin-bottom: 1.15rem;
    }}
    .comet-section-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: #1976d2;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 0.13rem;
        letter-spacing: 0.5px;
    }}
    .comet-summary {{
        font-size: 1rem;
        color: #232323;
        line-height: 1.6;
        text-align: justify;
    }}
    .comet-skills {{
        font-size: 0.97rem;
        color: #232323;
        margin-bottom: 0.2rem;
    }}
    .comet-item {{
        margin-bottom: 0.95rem;
    }}
    .comet-item-header {{
        font-size: 1.01rem;
        font-weight: 500;
        color: #232323;
        margin-bottom: 0.13rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        align-items: baseline;
    }}
    .comet-item-title {{
        font-weight: 700;
    }}
    .comet-item-tech {{
        font-size: 0.95rem;
        color: #1976d2;
        margin-left: 0.6rem;
    }}
    .comet-item-description {{
        font-size: 0.97rem;
        color: #232323;
        margin-left: 0.1rem;
        margin-top: 0.15rem;
        line-height: 1.6;
        text-align: justify;
    }}
    .comet-interests {{
        font-size: 0.97rem;
        color: #232323;
        margin-bottom: 0.2rem;
    }}
    '''
    return css
