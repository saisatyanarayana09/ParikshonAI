# Parikshon AI Project Overview

## Project Name

Parikshon AI

## Short Description

Parikshon AI is a Django-based AI document assistant. It lets users upload documents and perform AI-powered actions such as summarization, document chat, OCR text extraction, keyword extraction, and quiz generation.

The project preserves a traditional Django architecture and uses Django templates, custom CSS, and vanilla JavaScript for the frontend.

## Current Frontend

This project does not use React, Vue, Angular, or Next.js.

The frontend is built with:

- Django templates
- HTML
- Custom CSS
- Vanilla JavaScript

Important frontend files:

- `templates/base.html`
- `templates/core/home.html`
- `templates/core/summarize.html`
- `templates/core/chat.html`
- `templates/core/ocr.html`
- `templates/core/keywords.html`
- `templates/core/quiz.html`
- `templates/core/_upload_box.html`
- `templates/core/_document_info.html`
- `static/css/styles.css`
- `static/js/app.js`

## Backend Stack

The backend is built with:

- Django 4
- PostgreSQL (with pgvector for vector embeddings)
- Python
- LangChain
- Hugging Face Inference Providers (Qwen 2.5 7B Instruct)
- Hugging Face Transformers
- Sentence Transformers
- Tesseract OCR
- Poppler
- pdfplumber
- python-docx
- python-pptx
- pandas
- YAKE

## Main Features

### 1. Smart Summarizer

Users can upload a supported document and generate a summary.

Supported summary options include:

- Quick Summary
- Detailed Summary
- Bullet Summary
- Executive Summary
- Academic Summary
- Key Insights
- Action Items
- Important Points

Summary length options:

- Short
- Medium
- Long

Key files:

- `core/views.py`
- `core/forms.py`
- `core/utils/summarizer.py`
- `templates/core/summarize.html`

### 2. Chat With Document

Users can upload a document and ask questions about it.

The chat flow:

1. Upload document
2. Extract text
3. Split text into chunks
4. Create embeddings
5. Store embeddings with their document chunks in MySQL
6. Retrieve relevant chunks for a user question
7. Send context to a Hugging Face hosted instruction model
8. Return a grounded answer

Key files:

- `core/views.py`
- `core/models.py`
- `core/utils/chat.py`
- `templates/core/chat.html`

### 3. OCR Text Extractor

Users can extract text from scanned PDFs, images, and other supported documents.

For scanned PDFs and images, OCR depends on:

- Tesseract
- Poppler

Key files:

- `core/utils/extractor.py`
- `core/utils/ocr.py`
- `templates/core/ocr.html`

### 4. Keyword Extractor

Users can upload a document and extract important keywords and phrases.

The project uses:

- YAKE
- scikit-learn stop words
- frequency counting

Key files:

- `core/utils/keywords.py`
- `templates/core/keywords.html`

### 5. Quiz Generator

Users can upload a document and generate a five-question multiple-choice quiz.

The quiz is generated using a Hugging Face hosted instruction model.

Key files:

- `core/utils/quiz.py`
- `templates/core/quiz.html`

## Supported Upload Types

The project supports:

- PDF
- DOCX
- PPTX
- TXT
- CSV
- JPG
- JPEG
- PNG
- WEBP

Upload size limit:

- 10MB

Upload validation is handled in:

- `core/forms.py`

## Project Structure

```text
parikshon_ai/
  manage.py
  requirements.txt
  README.md
  .env.example
  PROJECT_OVERVIEW_FOR_CHATGPT.md

  parikshon_ai/
    settings.py
    urls.py
    wsgi.py
    asgi.py

  core/
    admin.py
    apps.py
    forms.py
    models.py
    urls.py
    views.py
    migrations/
    templatetags/
      core_extras.py
    utils/
      chat.py
      extractor.py
      files.py
      keywords.py
      ocr.py
      quiz.py
      summarizer.py

  templates/
    base.html
    core/
      home.html
      summarize.html
      chat.html
      ocr.html
      keywords.html
      quiz.html
      _upload_box.html
      _document_info.html

  static/
    css/
      styles.css
    js/
      app.js

  # Document chunks and embeddings are stored in MySQL
```

## Important Django Models

### ChatSession

Stores an uploaded chat document session.

Fields include:

- `id`
- `document_name`
- `extracted_text`
- Document chunks and embeddings are stored in related `DocumentChunk` records.
- `created_at`
- `updated_at`

### ChatMessage

Stores questions and answers for a chat session.

Fields include:

- `session`
- `question`
- `answer`
- `created_at`

Model file:

- `core/models.py`

## Important Settings

Settings file:

- `parikshon_ai/settings.py`

Important environment variables:

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
CSRF_TRUSTED_ORIGINS=
HUGGINGFACE_API_KEY=
HUGGINGFACE_CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct-1M
```

Example environment file:

- `.env.example`

## Local Setup

Recommended setup (Requires a running PostgreSQL instance with the `pgvector` extension):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

## External Dependencies

For OCR features:

- Tesseract must be installed and available on PATH.
- Poppler must be installed and available on PATH.

For AI features:

- `HUGGINGFACE_API_KEY` is required for document chat and quiz generation.
- `HUGGINGFACE_API_KEY` is optional unless model downloads require authentication.

## Current UI/UX Design

The project has been redesigned into a premium AI SaaS-style interface.

Current UI features include:

- Dark theme by default
- Light theme switcher
- Responsive navigation
- Premium workspace layout
- Drag-and-drop upload zone
- Upload progress animation
- Processing stages
- Document information panel
- Chat-style document Q&A interface
- Copy buttons
- Keyword filtering
- OCR text search highlighting
- Responsive mobile layout

## Current Limitations

Some advanced features are partially represented in the UI but not fully implemented in the backend yet.

Examples:

- True global semantic search across all uploaded documents
- Persistent document dashboard shared across all tools
- Chat rename/delete actions
- Source citations with exact document references
- OCR confidence scoring
- Real streaming responses
- Markdown rendering for chat responses
- User authentication/profile system

## Notes For ChatGPT

If using this file to ask ChatGPT for help, useful prompts include:

- "Analyze this Django project and suggest improvements."
- "Help me add global semantic search to this project."
- "Help me implement persistent uploaded document management."
- "Help me add source citations to document chat."
- "Help me convert this Django template frontend to React."
- "Help me deploy this Django AI app."
- "Help me add tests for the main AI workflows."
