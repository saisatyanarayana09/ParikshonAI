import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageEnhance

def order_points(pts):
    # Initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype="float32")
    
    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    
    # compute the width of the new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    
    # compute the height of the new image
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
        
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    
    return warped

def process_document(image_bytes: bytes, brightness: float = 1.0, contrast: float = 1.0, saturation: float = 1.0) -> bytes:
    """
    Takes an image in bytes, applies the enhancement pipeline and adjustments,
    and returns the enhanced image in bytes (JPEG).
    """
    # 1. Read image from bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image")

    orig = image.copy()
    
    # 2. Pad the image to ensure document edges form closed contours even if they touch the image border
    pad = 10
    padded = cv2.copyMakeBorder(image, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    
    gray = cv2.cvtColor(padded, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)

    # 3. Find all contours in the padded image
    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    screenCnt = None
    image_area = image.shape[0] * image.shape[1]
    
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        # Prefer a perfect 4-point convex polygon (like a clean sheet of paper)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            if cv2.contourArea(approx) > 0.15 * image_area:
                screenCnt = approx - pad
                break
                
    # Fallback: If no perfect 4 points were found (e.g., covered by fingers or plastic sleeve),
    # just find the tightest bounding rectangle (minAreaRect) around the largest contour.
    if screenCnt is None and len(cnts) > 0:
        largest_c = cnts[0]
        if cv2.contourArea(largest_c) > 0.15 * image_area:
            rect = cv2.minAreaRect(largest_c)
            box = cv2.boxPoints(rect)
            screenCnt = np.intp(box) - pad

    # 4. Perspective transform (Auto Crop & Deskew)
    if screenCnt is not None:
        warped = four_point_transform(orig, screenCnt.reshape(4, 2))
    else:
        warped = orig

    # 5. "Magic Color" Enhancement: Remove shadows and make background pure white while preserving color
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    
    # Estimate the background illumination using morphological dilation
    # This effectively erases the dark text, leaving only the paper's shadow profile
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    bg = cv2.dilate(warped_gray, kernel)
    bg = cv2.GaussianBlur(bg, (21, 21), 0)
    
    # Prevent division by zero
    bg = np.maximum(bg, 1)
    
    warped_float = warped.astype(np.float32)
    bg_bgr = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR).astype(np.float32)
    
    # Divide the image by its background to normalize lighting (shadows become white)
    magic = np.clip((warped_float / bg_bgr) * 255, 0, 255).astype(np.uint8)

    # Convert back to PIL Image to apply granular enhancements
    pil_img = Image.fromarray(cv2.cvtColor(magic, cv2.COLOR_BGR2RGB))
    
    # Apply Sliders
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(pil_img)
        pil_img = enhancer.enhance(brightness)
        
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(contrast)
        
    if saturation != 1.0:
        enhancer = ImageEnhance.Color(pil_img)
        pil_img = enhancer.enhance(saturation)

    out_io = BytesIO()
    # Save as highly compressed PNG or high-quality JPEG
    pil_img.save(out_io, format='JPEG', quality=90)
    
    return out_io.getvalue()
