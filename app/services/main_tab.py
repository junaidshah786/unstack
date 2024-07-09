import pypdfium2 as pdfium


# Function to convert PDF to images using pypdfium2
def pdf_to_images(pdf_path):
    pdf = pdfium.PdfDocument(pdf_path)
    images = []
    for i in range(len(pdf)):
        page = pdf[i]
        bitmap = page.render(scale=1, rotation=0)
        pil_image = bitmap.to_pil()
        images.append(pil_image)
    return images

# Function to display PDF as images
def display_pdf(images):
    for image in images:
        st.image(image, use_column_width=True)