import io
import zipfile
from pypdf import PdfReader, PdfWriter
from PIL import Image
from pdf2image import convert_from_bytes
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def merge_pdfs(files):
    writer = PdfWriter()
    for file in files:
        reader = PdfReader(file)
        for page in reader.pages:
            writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def split_pdf(file, start_page, end_page):
    reader = PdfReader(file)
    writer = PdfWriter()
    total = len(reader.pages)
    
    start = max(0, start_page - 1)
    end = min(total, end_page)
    
    for i in range(start, end):
        writer.add_page(reader.pages[i])
        
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def protect_pdf(file, password):
    reader = PdfReader(file)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    
    writer.encrypt(password)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def unlock_pdf(file, password):
    reader = PdfReader(file)
    if reader.is_encrypted:
        success = reader.decrypt(password)
        if not success:
            raise ValueError("Incorrect password")
            
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
        
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def rotate_pdf(file, degrees):
    reader = PdfReader(file)
    writer = PdfWriter()
    
    for page in reader.pages:
        page.rotate(degrees)
        writer.add_page(page)
        
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def remove_pages(file, pages_to_remove):
    reader = PdfReader(file)
    writer = PdfWriter()
    
    for i, page in enumerate(reader.pages):
        if (i + 1) not in pages_to_remove:
            writer.add_page(page)
            
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def jpg_to_pdf(image_files):
    images = []
    for f in image_files:
        img = Image.open(f).convert("RGB")
        images.append(img)
        
    if not images:
        return b""
        
    out = io.BytesIO()
    images[0].save(out, format="PDF", save_all=True, append_images=images[1:])
    out.seek(0)
    return out.read()

def pdf_to_jpg(file):
    images = convert_from_bytes(file.read())
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for i, img in enumerate(images):
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="JPEG")
            zf.writestr(f"page_{i+1}.jpg", img_buffer.getvalue())
            
    zip_buffer.seek(0)
    return zip_buffer.read()

def pdf_to_text(file):
    reader = PdfReader(file)
    text = ""
    for i, page in enumerate(reader.pages):
        text += f"--- Page {i+1} ---\n"
        text += page.extract_text() or ""
        text += "\n\n"
        
    return text.encode('utf-8')

def watermark_pdf(file, text):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", 40)
    can.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
    can.saveState()
    can.translate(300, 400)
    can.rotate(45)
    can.drawCentredString(0, 0, text)
    can.restoreState()
    can.save()
    packet.seek(0)
    watermark = PdfReader(packet).pages[0]

    reader = PdfReader(file)
    writer = PdfWriter()
    
    for page in reader.pages:
        page.merge_page(watermark)
        writer.add_page(page)
        
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def add_page_numbers(file):
    reader = PdfReader(file)
    writer = PdfWriter()
    
    total = len(reader.pages)
    for i, page in enumerate(reader.pages):
        packet = io.BytesIO()
        can = canvas.Canvas(packet)
        can.setFont("Helvetica", 10)
        can.drawString(290, 20, f"Page {i+1} of {total}")
        can.save()
        packet.seek(0)
        
        number_pdf = PdfReader(packet).pages[0]
        page.merge_page(number_pdf)
        writer.add_page(page)
        
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def compress_pdf(file):
    reader = PdfReader(file)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
        
    for page in writer.pages:
        page.compress_content_streams()
        
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()
