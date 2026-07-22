# Parikshon AI

Parikshon AI is a Django 4 document intelligence platform with five production-facing AI modules:

- Smart Summarizer using `facebook/bart-large-cnn`
- Chat with Document using MySQL-stored embeddings, sentence transformers, and Hugging Face Inference Providers
- OCR Text Extractor for scanned PDFs and images
- Keyword Extractor using YAKE with frequency counts
- Quiz Generator using Hugging Face Inference Providers

Supported uploads: PDF, scanned PDF, DOCX, PPTX, TXT, CSV, JPG, PNG, and WEBP. Files are limited to 10MB and are deleted immediately after text extraction or indexing.

## Requirements

- Python 3.10 or newer
- Tesseract OCR installed and available on PATH
- Poppler installed and available on PATH for scanned PDF OCR
- A Hugging Face access token for document chat and quiz generation
- Optional HuggingFace token for model downloads in restricted environments

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Edit `.env` before using AI modules:

```env
DJANGO_SECRET_KEY=use-a-long-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
HUGGINGFACE_API_KEY=your-huggingface-token
HUGGINGFACE_CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct-1M
```

`HUGGINGFACE_API_KEY` is required for Chat with Document and Quiz Generator. It is also used when downloading Hugging Face models in restricted environments.

## Installing OCR Dependencies

### Windows

Install Tesseract from the official Windows installer and add its install folder to PATH. Install Poppler for Windows and add the `bin` folder to PATH.

### macOS

```bash
brew install tesseract poppler
```

### Ubuntu or Debian

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

## Project Structure

```text
parikshon_ai/
  manage.py
  requirements.txt
  README.md
  .env.example
  parikshon_ai/
    settings.py
    urls.py
    wsgi.py
    asgi.py
  core/
    models.py
    forms.py
    views.py
    urls.py
    utils/
      extractor.py
      summarizer.py
      chat.py
      ocr.py
      keywords.py
      quiz.py
  templates/
    base.html
    core/
  static/
    css/styles.css
    js/app.js
  media/
  # Document chunks and embeddings are stored in MySQL
```

## Database

The application uses MySQL. Chat sessions, messages, document chunks, and chunk embeddings are stored in MySQL; no ChromaDB instance or local vector database is required.

Create the database before running migrations:

```sql
CREATE DATABASE parikshon_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Set the `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, and `MYSQL_PORT` values in `.env`, then run `python manage.py migrate`.

On Windows, this project uses PyMySQL as the MySQL driver; it is installed with `pip install -r requirements.txt`.

## Security and Validation

- Django CSRF protection is enabled on all forms.
- Upload extensions are validated server-side.
- Upload size is limited to 10MB.
- Temporary uploaded files are deleted after processing.
- User-facing errors are shown through Django messages.
- Production static serving is configured with WhiteNoise.
- `DEBUG` should be set to `False` before deployment.

## Production Deployment

1. Set production environment variables:

```env
DJANGO_SECRET_KEY=long-production-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
HUGGINGFACE_API_KEY=your-huggingface-token
HUGGINGFACE_CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct-1M
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run migrations and collect static files:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

4. Start with Gunicorn:

```bash
gunicorn parikshon_ai.wsgi:application --bind 0.0.0.0:8000
```

5. Put Nginx, Caddy, or your platform router in front of Gunicorn with HTTPS enabled.

Large model inference can be memory intensive. For production traffic, run at least 4GB RAM for light use and more if multiple summarization requests may run at the same time.
