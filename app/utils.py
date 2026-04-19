import os
import uuid
import bleach
from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_MIME_PREFIXES = {
    "image/": "image",
    "video/": "video",
    "audio/": "audio",
}
ALLOWED_FILE_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp",
    "mp4", "webm",
    "mp3", "wav", "m4a",
    "pdf", "txt", "zip", "hwp", "hwpx"
}
ALLOWED_TAGS = ["b", "i", "u", "strong", "em", "span", "br"]
ALLOWED_ATTRS = {"span": ["style"]}

def sanitize_html(html):
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_FILE_EXTENSIONS

def save_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("허용되지 않은 파일 형식입니다.")

    original_name = secure_filename(file_storage.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    upload_path = os.path.join(current_app.root_path, "static", current_app.config["UPLOAD_DIR"], stored_name)
    file_storage.save(upload_path)

    mime = file_storage.mimetype or "application/octet-stream"
    media_type = "file"
    for prefix, mapped in ALLOWED_MIME_PREFIXES.items():
        if mime.startswith(prefix):
            media_type = mapped
            break

    return {
        "file_name": original_name,
        "stored_name": stored_name,
        "mime_type": mime,
        "file_size": os.path.getsize(upload_path),
        "media_type": media_type,
    }