from datetime import datetime
import os
import tempfile
import uuid
from flask import send_file, current_app
from weasyprint import HTML, CSS

def format_description(text):
    """Convert newlines to HTML line breaks"""
    if not text:
        return ''
    # Replace newlines with <br> tags
    return text.replace('\n', '<br>')

def format_date(date_str):
    """Format date from YYYY-MM to Month YYYY"""
    if not date_str:
        return ''
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m')
        return date_obj.strftime('%B %Y')
    except ValueError:
        return date_str

def calcHeightModern1(data):
    """Calculate the height needed for the PDF based on content"""
    # Base height for header and margins
    height = 150

    # Add height for summary
    if data.get('summary'):
        height += 100

    # Add height for experience items
    if data.get('experience'):
        height += 50  # Section header
        height += len(data['experience']) * 150  # Each experience item

    # Add height for education items
    if data.get('education'):
        height += 50
        height += len(data['education']) * 100

    # Add height for projects
    if data.get('projects'):
        height += 50
        height += len(data['projects']) * 130  # Projects might have tech stack lists

    # Add height for skills
    if data.get('skills'):
        height += 100
        if data['skills'].get('programmingLanguages'):
            height += 30 + (len(data['skills']['programmingLanguages']) // 3) * 30
        if data['skills'].get('keywords'):
            height += 30 + (len(data['skills']['keywords']) // 3) * 30

    # Add height for languages
    if data.get('languages'):
        height += 50 + (len(data['languages']) // 3) * 30

    # Add height for certifications
    if data.get('certifications'):
        height += 50
        height += len(data['certifications']) * 80

    # Add height for awards
    if data.get('awards'):
        height += 50
        height += len(data['awards']) * 100

    # Add height for interests
    if data.get('interests'):
        height += 50 + (len(data['interests']) // 3) * 30

    # Add height for references
    if data.get('references'):
        height += 50
        height += len(data['references']) * 120

    # Add some buffer for safety
    height += 100

    return height

def export_pdf_response(html_content, css_content, output_filename=None):
    """
    Render HTML+CSS to PDF and return a Flask send_file response.
    """
    try:
        temp_dir = tempfile.gettempdir()
        filename = output_filename or f"resume_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(temp_dir, filename)
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string=css_content)]
        )
        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=filename
        )
    except Exception as e:
        current_app.logger.error(f"PDF export error: {str(e)}")
        return {"error": f"Failed to export PDF: {str(e)}"}, 500