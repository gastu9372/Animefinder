from src.core.security import detect_image_type, is_allowed_image


def test_detect_jpeg_magic_bytes() -> None:
    # JPEG mínimo con magic bytes \xFF\xD8\xFF y bytes de relleno
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01"
    assert detect_image_type(jpeg_bytes) == "jpeg"
    assert is_allowed_image(jpeg_bytes) is True


def test_detect_png_magic_bytes() -> None:
    # PNG mínimo con magic bytes \x89PNG\r\n\x1a\n
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    assert detect_image_type(png_bytes) == "png"
    assert is_allowed_image(png_bytes) is True


def test_detect_webp_magic_bytes() -> None:
    # WebP: 'RIFF' + 4 bytes longitud + 'WEBP'
    webp_bytes = b"RIFF\x24\x00\x00\x00WEBPVP8 "
    assert detect_image_type(webp_bytes) == "webp"
    assert is_allowed_image(webp_bytes) is True


def test_reject_executable_and_plain_text() -> None:
    # Ejecutable Windows MZ
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"
    assert detect_image_type(exe_bytes) is None
    assert is_allowed_image(exe_bytes) is False

    # Archivo de texto plano
    txt_bytes = b"Hello, this is just a plain text file, not an image."
    assert detect_image_type(txt_bytes) is None
    assert is_allowed_image(txt_bytes) is False

    # Buffer demasiado corto
    short_bytes = b"GIF89a"
    assert detect_image_type(short_bytes) is None
    assert is_allowed_image(short_bytes) is False
