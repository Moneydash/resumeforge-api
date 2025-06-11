from datetime import datetime
import math
import os
import tempfile
import uuid
from flask import send_file, current_app
from weasyprint import HTML, CSS
import logging
import json
import hashlib

def format_description(text):
    """Format description as HTML: preserve lists, convert newlines to <br> for plain text."""
    if not text:
        return ''
    # If already contains a list, return as-is (assume HTML is safe/trusted)
    if '<ul' in text or '<ol' in text:
        return text
    # Otherwise, treat as plain text and replace newlines
    return text.replace('</p>', '</p><br>').replace('\n', '<br>')

def format_date(date_str):
    """Format date from YYYY-MM to Month YYYY"""
    if not date_str:
        return ''
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m')
        return date_obj.strftime('%B %Y')
    except ValueError:
        return date_str

def filename_generator(name):
    text_split = name.split()
    text_join = '-'.join(text_split)
    return text_join

def css_height_calc(html_content, css_content, email, template, buffer, max_attempts=50, increment=50):
    redis_client = current_app.redis_client
    cache_key_content = f"{email}_content_height_{template}"

    # Get cached values if they exist
    cached_content_height = redis_client.get(cache_key_content)

    # Always get current content height from a no-height CSS
    html = HTML(string=html_content)
    initial_render = html.render(stylesheets=[CSS(string=css_content(1009))])
    content_height = round(initial_render.pages[0].height, 2)
    buff_height = content_height * buffer
    content_height = max(content_height + buff_height, 100)

    redis_client.set(cache_key_content, content_height)

    logging.info(f"Content Height: {content_height}")
    logging.info(f"Cached Content Height: {cached_content_height}")
    logging.info(f"number of Pages: {len(initial_render.pages)}")
    logging.info(f"Buffer: {buffer}")
    if len(initial_render.pages) > 1:
        final_height = loop_process(
            html_content=html_content,
            css_content=css_content,
            email=email,
            template=template,
            content_height=content_height,
            redis_client=redis_client,
            max_attempts=max_attempts,
            increment=increment
        )
    else:
        final_height = content_height

    return css_content(dynamic_height=final_height)

def loop_process(html_content, css_content, email, template, content_height,
                 redis_client, max_attempts=50, increment=50):
    min_height = 1009  # never go below this
    content_height = max(content_height, min_height)
    logging.info(f"Content Height loop process: {content_height}")

    initial_target = math.ceil(content_height)
    height_diff = initial_target - min_height
    final_height = abs(height_diff) + min_height

    logging.info(f"Diff me: {height_diff}")
    logging.info(f"[🔍] Loop starting. Est height: {final_height}pt")

    for i in range(max_attempts):
        css = css_content(dynamic_height=final_height)
        rendered = HTML(string=html_content).render(stylesheets=[CSS(string=css)])

        if len(rendered.pages) == 1:
            logging.info(f"[✅] Final height: {final_height}pt in {i + 1} loop(s)")
            redis_client.set(f"{email}_css_height_{template}", final_height)
            break

        final_height += increment
        logging.info(f"[↗] Page overflow, increased to {final_height}pt")

    return final_height

def data_caching(data, template_name="andromeda"):
    """
    Check if data has changed. If not, return cached PDF path.
    Otherwise, return None to signal a regeneration is needed.
    """
    email = data.get('personal', {}).get('email')
    if not email:
        return None

    redis_client = current_app.redis_client

    combined_data = {
        "template": template_name,
        "resume_data": data
    }

    # Hash the data for comparison
    data_str = json.dumps(combined_data, sort_keys=True)
    data_hash = hashlib.sha256(data_str.encode()).hexdigest()

    cache_key_hash = f"{email}_data_hash_{template_name}"
    cache_key_pdf = f"{email}_pdf_path_{template_name}"

    cached_hash = redis_client.get(cache_key_hash)
    cached_pdf_path = redis_client.get(cache_key_pdf)

    if cached_hash and cached_pdf_path and cached_hash == data_hash:
        return cached_pdf_path  # You can call `send_file` in your main route
    else:
        return None  # Indicates data changed or no cache

def get_output_path(name, template_name):
    filename = f"{filename_generator(name)}_{template_name}"
    return os.path.join(tempfile.gettempdir(), f"{filename}.pdf")