import io
import zipfile
from pypdf import PdfReader, PdfWriter
from PIL import Image
from pdf2image import convert_from_bytes
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4, landscape

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

def split_pdf(file, start_page, end_page, mode="range"):
    reader = PdfReader(file)
    total = len(reader.pages)
    
    start = max(0, start_page - 1)
    end = min(total, end_page)
    
    if mode == "range":
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])
            
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read(), "application/pdf", "split.pdf"
    
    elif mode == "single":
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for i in range(start, end):
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                page_buffer = io.BytesIO()
                writer.write(page_buffer)
                zf.writestr(f"page_{i+1}.pdf", page_buffer.getvalue())
        zip_buffer.seek(0)
        return zip_buffer.read(), "application/zip", "split_pages.zip"

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

def rotate_pdf(file, degrees, apply_to="all"):
    reader = PdfReader(file)
    writer = PdfWriter()
    
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        if apply_to == "all" or (apply_to == "even" and page_num % 2 == 0) or (apply_to == "odd" and page_num % 2 != 0):
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

def jpg_to_pdf(image_files, orientation="portrait", margin="none"):
    images = []
    
    margin_px = 0
    if margin == "small":
        margin_px = 40
    elif margin == "large":
        margin_px = 100
        
    for f in image_files:
        img = Image.open(f).convert("RGB")
        
        # Determine target size (A4)
        target_size = (595, 842) # A4 at 72dpi
        if orientation == "landscape":
            target_size = (842, 595)
            
        # Create a blank white canvas of target size
        bg = Image.new("RGB", target_size, (255, 255, 255))
        
        # Resize image to fit within canvas minus margins
        max_w = target_size[0] - (2 * margin_px)
        max_h = target_size[1] - (2 * margin_px)
        
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        
        # Center the image
        offset = ((target_size[0] - img.width) // 2, (target_size[1] - img.height) // 2)
        bg.paste(img, offset)
        
        images.append(bg)
        
    if not images:
        return b""
        
    out = io.BytesIO()
    images[0].save(out, format="PDF", save_all=True, append_images=images[1:])
    out.seek(0)
    return out.read()

def pdf_to_jpg(file, quality="high"):
    dpi = 150
    if quality == "standard":
        dpi = 72
    elif quality == "maximum":
        dpi = 300
        
    images = convert_from_bytes(file.read(), dpi=dpi)
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for i, img in enumerate(images):
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="JPEG", quality=95)
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

def watermark_pdf(file, text, position="center", opacity=50, rotation=45):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 60)
    
    alpha = opacity / 100.0
    can.setFillColorRGB(0.5, 0.5, 0.5, alpha=alpha)
    can.saveState()
    
    # Coordinates (Letter size is 612 x 792)
    x, y = 306, 396
    if position == "top-left": x, y = 150, 650
    elif position == "top-right": x, y = 450, 650
    elif position == "bottom-left": x, y = 150, 150
    elif position == "bottom-right": x, y = 450, 150
    
    can.translate(x, y)
    can.rotate(rotation)
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

def add_page_numbers(file, position="bottom-center", format_type="number"):
    reader = PdfReader(file)
    writer = PdfWriter()
    
    total = len(reader.pages)
    for i, page in enumerate(reader.pages):
        packet = io.BytesIO()
        # Get page size to correctly position text
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        
        can = canvas.Canvas(packet, pagesize=(width, height))
        can.setFont("Helvetica", 12)
        
        text = str(i+1)
        if format_type == "page-n": text = f"Page {i+1}"
        elif format_type == "n-of-m": text = f"Page {i+1} of {total}"
        
        x, y = width / 2.0, 30
        if position == "bottom-left": x = 30
        elif position == "bottom-right": x = width - 80
        elif position == "top-center": y = height - 30
        elif position == "top-left": x, y = 30, height - 30
        elif position == "top-right": x, y = width - 80, height - 30
        
        can.drawString(x, y, text)
        can.save()
        packet.seek(0)
        
        number_pdf = PdfReader(packet).pages[0]
        page.merge_page(number_pdf)
        writer.add_page(page)
        
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def compress_pdf(file, level="basic"):
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
