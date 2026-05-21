from PIL import Image, ImageFilter, ImageOps


def preprocess_ocr_image(pil_img, ocr_lang):
    """
    V1.0.5:
    Improve OCR for small Japanese Katakana by enlarging, grayscaling,
    increasing contrast and sharpening the capture image before Tesseract.
    Returns processed image and scale factor for coordinate correction.
    """
    scale = 2 if "jpn" in ocr_lang else 1

    img = pil_img.convert("L")

    if scale != 1:
        img = img.resize(
            (img.width * scale, img.height * scale),
            Image.Resampling.LANCZOS
        )

    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)

    return img, scale
