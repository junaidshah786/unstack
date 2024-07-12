import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.config import unstract_key

def call_unstract_api_dummy():
    return """

**Subject: Request for Leave**

I am writing to request a leave of absence from school for [number of days] days, from [start date] to [end date]. The reason for this leave is [provide a brief reason, such as "due to a family event," "medical reasons," or "personal reasons"].

I assure you that I will make every effort to catch up on any missed assignments and classwork during my absence. I will also coordinate with my teachers to ensure that I stay on track with my studies.

I kindly request your approval for this leave and would be grateful for your understanding and support.

Thank you for considering my request.

Yours sincerely,

[Your Name]  
[Your Contact Information, if needed]

"""


# Function to create a new PDF with the extracted text
def create_text_pdf(text, output_pdf_path):
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter

    lines = text.split('\n')
    y = height - 40  # Start drawing 40 units from the top

    for line in lines:
        c.drawString(30, y, line)
        y -= 14  # Move 14 units down for each new line

    c.save()
    

# Function to call the Unstract API
def call_unstract_api(pdf_file_path):
    url = 'https://llmwhisperer-api.unstract.com/v1/whisper?processing_mode=ocr&output_mode=line-printer&force_text_processing=false&page_seperator=%3C%3C%3C&timeout=200&store_metadata_for_highlighting=true&median_filter_size=0&gaussian_blur_radius=0&ocr_provider=simple&line_splitter_tolerance=0.4&horizontal_stretch_factor=1'
    headers = {
        'accept': 'text/plain',
        'unstract-key': unstract_key,
        'Content-Type': 'application/octet-stream'
    }

    with open(pdf_file_path, 'rb') as f:
        response = requests.post(url, headers=headers, data=f)

    if response.status_code == 200:
        return response.text
    else:
        response.raise_for_status()