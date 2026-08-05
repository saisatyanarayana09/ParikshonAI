import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageEnhance
import logging

logger = logging.getLogger(__name__)

def order_points(pts):
    """
    Orders coordinates in the following order:
    Top-left, Top-right, Bottom-right, Bottom-left.
    """
    rect = np.zeros((4, 2), dtype="float32")
    
    # Top-left has the smallest sum, Bottom-right has the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Top-right has the smallest difference, Bottom-left has the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def four_point_transform(image, pts):
    """
    Applies a perspective transform to obtain a top-down, "birds-eye" view.
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Compute the width of the new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # Compute the height of the new image
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # Construct destination points for the warp
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # Calculate the perspective transform matrix and warp
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    
    return warped

def find_document_contour(image, max_dim=800):
    """
    Detects the document in the image. Optimizes performance by resizing 
    large images before edge detection, while returning coordinates scaled 
    to the original image size.
    """
    # 1. Resize for performance and better edge detection
    h, w = image.shape[:2]
    ratio = 1.0
    if h > max_dim or w > max_dim:
        ratio = h / float(max_dim) if h > w else w / float(max_dim)
        small = cv2.resize(image, (int(w / ratio), int(h / ratio)))
    else:
        small = image.copy()

    # 2. Add padding to guarantee closed contours if document touches the border
    pad = 10
    padded = cv2.copyMakeBorder(small, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=[0, 0, 0])

    # 3. Grayscale and Bilateral Filtering
    # Bilateral filter removes noise (like fabric patterns) while keeping edges sharp
    gray = cv2.cvtColor(padded, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    # 4. Edge Detection
    edged = cv2.Canny(gray, 30, 200)

    # Dilate edges slightly to close any small gaps (e.g. from plastic glare)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edged = cv2.dilate(edged, kernel, iterations=1)

    # 5. Contour Extraction
    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    screenCnt = None
    image_area = small.shape[0] * small.shape[1]

    # 6. Find the best contour
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # Criteria A: Perfect 4-point convex polygon, area > 10% of image
        if len(approx) == 4 and cv2.isContourConvex(approx) and cv2.contourArea(approx) > 0.10 * image_area:
            screenCnt = approx
            break

    # 7. Fallback: Minimum Area Rectangle for the largest valid contour
    # Handles cases where fingers break the document border
    if screenCnt is None and len(cnts) > 0:
        largest_c = cnts[0]
        if cv2.contourArea(largest_c) > 0.10 * image_area:
            rect = cv2.minAreaRect(largest_c)
            box = cv2.boxPoints(rect)
            screenCnt = np.intp(box)

    # 8. Scale points back to original image resolution
    if screenCnt is not None:
        # Remove the padding offset first, then multiply by the resize ratio
        screenCnt = (screenCnt - pad) * ratio
        return screenCnt
        
    return None

def enhance_lighting(image):
    """
    Applies professional 'Scanner App' effects: background whitening, 
    shadow removal, contrast optimization, and text sharpening.
    """
    # Convert to LAB color space to process illumination (L) without distorting colors (A, B)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # 1. Shadow Removal & Background Whitening
    # Morphological dilation erases dark text, leaving only the shadow profile of the paper
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    bg = cv2.dilate(l, kernel)
    bg = cv2.GaussianBlur(bg, (21, 21), 0)
    bg = np.maximum(bg, 1)  # Prevent division by zero

    # Normalize the lighting by dividing the L channel by the background shadow map
    l_float = l.astype(np.float32)
    bg_float = bg.astype(np.float32)
    l_normalized = np.clip((l_float / bg_float) * 255, 0, 255).astype(np.uint8)

    # 2. Contrast Enhancement (Adaptive)
    # CLAHE adds punchy contrast, ensuring text is dark and paper is uniformly white
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l_normalized)

    # Merge channels and convert back to BGR
    merged = cv2.merge((l_enhanced, a, b))
    color_enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    # 3. Text Sharpening (Unsharp Masking)
    # Subtly sharpens the image to mimic a high-quality scanner
    gaussian = cv2.GaussianBlur(color_enhanced, (0, 0), 2.0)
    sharpened = cv2.addWeighted(color_enhanced, 1.5, gaussian, -0.5, 0)

    return sharpened

def process_document(image_bytes: bytes, brightness: float = 1.0, contrast: float = 1.0, saturation: float = 1.0) -> bytes:
    """
    Main processing pipeline. Fully in-memory, handles resizing, cropping, 
    lighting enhancements, and granular PIL adjustments.
    """
    try:
        # 1. Decode bytes directly to OpenCV array (supports JPG, PNG, WebP, BMP)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Invalid or corrupted image file format.")

        # 2. Document Detection & Cropping
        pts = find_document_contour(image)
        if pts is not None:
            warped = four_point_transform(image, pts.reshape(4, 2))
        else:
            # Graceful fallback: Apply enhancements to the full image if no document is detected
            warped = image.copy()

        # 3. Scanner-Style Enhancement Pipeline
        enhanced_cv = enhance_lighting(warped)

        # 4. Apply Granular User Adjustments via Pillow
        pil_img = Image.fromarray(cv2.cvtColor(enhanced_cv, cv2.COLOR_BGR2RGB))
        
        if brightness != 1.0:
            pil_img = ImageEnhance.Brightness(pil_img).enhance(brightness)
        if contrast != 1.0:
            pil_img = ImageEnhance.Contrast(pil_img).enhance(contrast)
        if saturation != 1.0:
            pil_img = ImageEnhance.Color(pil_img).enhance(saturation)

        # 5. Output to memory buffer
        out_io = BytesIO()
        pil_img.save(out_io, format='JPEG', quality=90)
        return out_io.getvalue()
        
    except Exception as e:
        logger.error(f"Document enhancement failed: {str(e)}")
        raise
