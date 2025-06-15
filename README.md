# Resume Builder Backend

A Flask-based backend API for generating beautiful, professional PDF resumes from structured JSON data. Features multiple modern, minimal, and creative resume templates, with support for easy integration into React Native or other frontend applications.

## Features
- Multiple PDF resume templates: classic-modern, minimal, creative, and more
- Clean, readable, and professional designs
- Dynamic height calculation for optimal PDF layout
- RESTful API endpoints for PDF generation and export
- WeasyPrint for high-quality HTML/CSS to PDF rendering
- Easily extendable with new templates

## Endpoints

| Endpoint                        | Method | Description                                      |
|---------------------------------|--------|--------------------------------------------------|
| `/api/pdf/andromeda/generate`   | POST   | Generate PDF (Modern template)                   |
| `/api/pdf/cigar/generate`       | POST   | Generate PDF (Classic-Modern template)           |
| `/api/pdf/comet/generate`       | POST   | Generate PDF (Minimal template)                  |
| `/api/pdf/milky_way/generate`   | POST   | Generate PDF (Creative template)                 |
| `/api/pdf/zeus/generate`        | POST   | Generate PDF (Zeus template)                     |
| `/api/pdf/athena/generate`      | POST   | Generate PDF (Athena template)                   |
| `/api/pdf/apollo/generate`      | POST   | Generate PDF (Apollo template)                   |
| `/api/pdf/artemis/generate`     | POST   | Generate PDF (Artemis template)                  |

## Usage

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the server:**
   ```bash
   python main.py
   ```
3. **Send a POST request** to the desired endpoint with your resume data as JSON.

## Project Structure
- `api/controller/v1/` — PDF template controllers
- `api/routes/v1/pdf.py` — API route definitions
- `utils/helper.py` — Shared helpers (date formatting, PDF export, etc.)
- `main.py` — App entrypoint and blueprint registration

## License
This project is licensed under the [Open Fair License](./LICENSE).

---

### Credits
- [WeasyPrint](https://weasyprint.org/) for PDF rendering
- [Flask](https://flask.palletsprojects.com/) for the backend framework
- [Google Fonts](https://fonts.google.com/) for beautiful typography

---

For questions or contributions, open an issue or pull request!
