import os
import uuid
import base64
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.files.storage import FileSystemStorage
from .services import process_document

def enhancer_view(request):
    if request.method == "POST":
        file = request.FILES.get('image')
        if not file:
            return render(request, "document_enhancer/enhancer.html", {"error": "Please upload an image."})
            
        try:
            image_bytes = file.read()
            processed_bytes = process_document(image_bytes)
            
            # Save to MEDIA_ROOT
            enhancements_dir = os.path.join(settings.MEDIA_ROOT, 'enhancements')
            os.makedirs(enhancements_dir, exist_ok=True)
            fs = FileSystemStorage(location=enhancements_dir)
            
            # Generate unique filenames
            unique_id = uuid.uuid4().hex
            orig_filename = f"orig_{unique_id}.jpg"
            enhanced_filename = f"enhanced_{unique_id}.jpg"
            
            # We don't necessarily have to write the original, but requirements said "save both"
            file.seek(0)
            fs.save(orig_filename, file)
            # Create a file-like object for the processed bytes
            from django.core.files.base import ContentFile
            enhanced_path = fs.save(enhanced_filename, ContentFile(processed_bytes))
            
            orig_url = f"{settings.MEDIA_URL}enhancements/{orig_filename}"
            enhanced_url = f"{settings.MEDIA_URL}enhancements/{enhanced_path}"
            
            return render(request, "document_enhancer/enhancer.html", {
                "orig_url": orig_url,
                "enhanced_url": enhanced_url,
                "download_url": enhanced_url,
            })
            
        except Exception as e:
            return render(request, "document_enhancer/enhancer.html", {"error": f"Error processing image: {str(e)}"})
            
    return render(request, "document_enhancer/enhancer.html")
