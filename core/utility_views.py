import io
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from .utils import pdf_tools

def merge_view(request):
    if request.method == "POST":
        files = request.FILES.getlist('files')
        if not files or len(files) < 2:
            return HttpResponseBadRequest("Please upload at least two PDF files.")
        
        try:
            output = pdf_tools.merge_pdfs(files)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="merged.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/merge.html")

def split_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        start = int(request.POST.get('start_page', 1))
        end = int(request.POST.get('end_page', 1))
        if not file:
            return HttpResponseBadRequest("Please upload a PDF file.")
            
        try:
            output = pdf_tools.split_pdf(file, start, end)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="split.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/split.html")

def protect_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        password = request.POST.get('password')
        if not file or not password:
            return HttpResponseBadRequest("File and password are required.")
            
        try:
            output = pdf_tools.protect_pdf(file, password)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="protected.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/protect.html")

def unlock_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        password = request.POST.get('password')
        if not file or not password:
            return HttpResponseBadRequest("File and password are required.")
            
        try:
            output = pdf_tools.unlock_pdf(file, password)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="unlocked.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/unlock.html")

def rotate_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        degrees = int(request.POST.get('degrees', 90))
        if not file:
            return HttpResponseBadRequest("File is required.")
            
        try:
            output = pdf_tools.rotate_pdf(file, degrees)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="rotated.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/rotate.html")

def remove_pages_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        pages_str = request.POST.get('pages')
        if not file or not pages_str:
            return HttpResponseBadRequest("File and comma-separated pages are required.")
            
        try:
            pages = [int(p.strip()) for p in pages_str.split(',')]
            output = pdf_tools.remove_pages(file, pages)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="pages_removed.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/remove_pages.html")

def jpg_to_pdf_view(request):
    if request.method == "POST":
        files = request.FILES.getlist('files')
        if not files:
            return HttpResponseBadRequest("Please upload at least one image.")
            
        try:
            output = pdf_tools.jpg_to_pdf(files)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="images.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/jpg_to_pdf.html")

def pdf_to_jpg_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        if not file:
            return HttpResponseBadRequest("File is required.")
            
        try:
            output = pdf_tools.pdf_to_jpg(file)
            response = HttpResponse(output, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="images.zip"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/pdf_to_jpg.html")

def pdf_to_text_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        if not file:
            return HttpResponseBadRequest("File is required.")
            
        try:
            output = pdf_tools.pdf_to_text(file)
            response = HttpResponse(output, content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="extracted.txt"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/pdf_to_text.html")

def watermark_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        text = request.POST.get('text', 'CONFIDENTIAL')
        if not file:
            return HttpResponseBadRequest("File is required.")
            
        try:
            output = pdf_tools.watermark_pdf(file, text)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="watermarked.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/watermark.html")

def add_page_numbers_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        if not file:
            return HttpResponseBadRequest("File is required.")
            
        try:
            output = pdf_tools.add_page_numbers(file)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="numbered.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/page_numbers.html")

def compress_view(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        if not file:
            return HttpResponseBadRequest("File is required.")
            
        try:
            output = pdf_tools.compress_pdf(file)
            response = HttpResponse(output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="compressed.pdf"'
            return response
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return render(request, "core/utilities/compress.html")
