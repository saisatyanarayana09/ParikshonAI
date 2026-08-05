import base64
from django.shortcuts import render
from django.http import HttpResponseBadRequest
from .services import process_document

def enhancer_view(request):
    if request.method == "POST":
        file = request.FILES.get('image')
        if not file:
            return render(request, "document_enhancer/enhancer.html", {"error": "Please upload an image."})
            
        try:
            image_bytes = file.read()
            processed_bytes = process_document(image_bytes)
            
            # Convert both images to Base64 data URIs so they don't need to be saved to disk
            # This completely bypasses the broken MEDIA_URL issue on production servers
            orig_b64 = base64.b64encode(image_bytes).decode('utf-8')
            enhanced_b64 = base64.b64encode(processed_bytes).decode('utf-8')
            
            # Determine mime type from original file, default to jpeg
            content_type = file.content_type if file.content_type else 'image/jpeg'
            # Force jpeg for the enhanced output since OpenCV service returns jpeg
            enhanced_content_type = 'image/jpeg'
            
            orig_url = f"data:{content_type};base64,{orig_b64}"
            enhanced_url = f"data:{enhanced_content_type};base64,{enhanced_b64}"
            
            return render(request, "document_enhancer/enhancer.html", {
                "orig_url": orig_url,
                "enhanced_url": enhanced_url,
                "download_url": enhanced_url,
            })
            
        except Exception as e:
            return render(request, "document_enhancer/enhancer.html", {"error": f"Error processing image: {str(e)}"})
            
    return render(request, "document_enhancer/enhancer.html")
