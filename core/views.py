import json

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import ChatQuestionForm, UploadForm
from .models import ChatMessage, ChatSession
from .utils.chat import ChatError, answer_question, build_document_index
from .utils.extractor import ExtractionError, extract_text
from .utils.files import safe_delete, save_temp_upload
from .utils.keywords import KeywordError, extract_keywords
from .utils.ocr import extract_ocr_text
from .utils.quiz import QuizError, generate_quiz, score_quiz

# Anonymous users may ask this many questions before being prompted to sign up
ANON_CHAT_LIMIT = 5


def home(request):
    return render(request, "core/home.html")


def _extract_from_upload(uploaded_file):
    temp_path = save_temp_upload(uploaded_file)
    try:
        return extract_text(temp_path, uploaded_file.name)
    finally:
        safe_delete(temp_path)


def _document_info(metadata):
    if not metadata:
        return {}
    words = metadata.get("words", 0) or 0
    extension = (metadata.get("extension") or "").replace(".", "").upper() or "Document"
    return {
        "filename": metadata.get("source", "Uploaded document"),
        "document_type": extension,
        "word_count": words,
        "character_count": metadata.get("characters", 0),
        "reading_time": max(1, round(words / 220)) if words else 1,
        "language": "English",
        "status": "Ready",
        "used_ocr": metadata.get("used_ocr", False),
    }


@require_http_methods(["POST"])
def global_upload_view(request):
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded_file = form.cleaned_data["file"]
        temp_path = save_temp_upload(uploaded_file)
        try:
            text, metadata = extract_text(temp_path, uploaded_file.name)

            # Ensure the session has a key so we can track anonymous uploads
            if not request.session.session_key:
                request.session.create()

            # Create a ChatSession linked to the user (or anonymous session)
            active_session = ChatSession.objects.create(
                document_name=uploaded_file.name,
                extracted_text=text,
                user=request.user if request.user.is_authenticated else None,
                session_key=None if request.user.is_authenticated else request.session.session_key,
            )
            build_document_index(text, active_session)

            # Save metadata to Django session
            request.session["active_document_name"] = uploaded_file.name
            request.session["active_document_text"] = text
            request.session["active_document_metadata"] = _document_info(metadata)
            request.session["active_document_chat_session_id"] = str(active_session.id)

            # Reset anonymous question counter for the new document
            request.session["anon_chat_count"] = 0

            # Clear old tool data
            request.session.pop("quiz_questions", None)
            request.session.pop("download_text", None)

            messages.success(request, f"Document '{uploaded_file.name}' loaded successfully!")
        except Exception as exc:
            messages.error(request, f"Upload failed: {exc}")
        finally:
            safe_delete(temp_path)
    else:
        messages.error(request, "Failed to upload. Please select a valid file under 10MB.")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "core:home"
    return redirect(next_url)


def clear_document_view(request):
    request.session.pop("active_document_name", None)
    request.session.pop("active_document_text", None)
    request.session.pop("active_document_metadata", None)
    request.session.pop("active_document_chat_session_id", None)
    request.session.pop("quiz_questions", None)
    request.session.pop("download_text", None)
    messages.info(request, "Active document cleared.")
    
    next_url = request.META.get("HTTP_REFERER") or "core:home"
    # If the user is on a detail page and clears the document, redirect to home to prevent error loops
    if any(path in next_url for path in ["/chat/", "/ocr/", "/keywords/", "/quiz/"]):
        return redirect("core:home")
    return redirect(next_url)


@require_http_methods(["GET", "POST"])
def chat_view(request):
    session_id = request.session.get("active_document_chat_session_id")
    metadata = request.session.get("active_document_metadata")

    if not session_id:
        return render(request, "core/chat.html", {"no_document": True})

    active_session = ChatSession.objects.filter(id=session_id).first()
    if not active_session:
        return render(request, "core/chat.html", {"no_document": True})

    # ── Anonymous limit check ─────────────────────────────────────────────────
    is_anon = not request.user.is_authenticated
    anon_count = request.session.get("anon_chat_count", 0)
    limit_reached = is_anon and anon_count >= ANON_CHAT_LIMIT
    anon_remaining = max(0, ANON_CHAT_LIMIT - anon_count) if is_anon else None

    if request.method == "POST":
        if limit_reached:
            messages.warning(
                request,
                f"You've used all {ANON_CHAT_LIMIT} free questions. Sign up to continue.",
            )
            return redirect("core:chat")

        form = ChatQuestionForm(request.POST)
        if form.is_valid():
            history = [(m.question, m.answer) for m in active_session.messages.all()]
            try:
                answer, sources = answer_question(
                    active_session, form.cleaned_data["question"], history
                )
                ChatMessage.objects.create(
                    session=active_session,
                    question=form.cleaned_data["question"],
                    answer=answer,
                    sources=sources,
                )
                active_session.save(update_fields=["updated_at"])

                # Increment anon counter only for unauthenticated users
                if is_anon:
                    request.session["anon_chat_count"] = anon_count + 1

                is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
                if is_ajax:
                    return JsonResponse({
                        "success": True, 
                        "answer": answer,
                        "sources": sources,
                        "limit_reached": (is_anon and request.session["anon_chat_count"] >= ANON_CHAT_LIMIT)
                    })

                messages.success(request, "Answer generated.")
            except ChatError as exc:
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "error": str(exc)}, status=400)
                messages.error(request, str(exc))
            except Exception as exc:
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "error": f"Unexpected error: {exc}"}, status=500)
                messages.error(request, f"Unexpected error: {exc}")
            return redirect("core:chat")

    question_form = ChatQuestionForm(initial={"session_id": active_session.id})
    return render(
        request,
        "core/chat.html",
        {
            "question_form": question_form,
            "active_session": active_session,
            "chat_messages": active_session.messages.all(),
            "document_info": metadata,
            "limit_reached": limit_reached,
            "anon_remaining": anon_remaining,
            "anon_limit": ANON_CHAT_LIMIT,
        },
    )


@require_http_methods(["GET"])
def ocr_view(request):
    session_id = request.session.get("active_document_chat_session_id")
    text = request.session.get("active_document_text")
    metadata = request.session.get("active_document_metadata")
    
    if not session_id or not text:
        return render(request, "core/ocr.html", {"no_document": True})
        
    request.session["download_text"] = text
    request.session["download_filename"] = "parikshon-ocr-text.txt"
    
    return render(
        request,
        "core/ocr.html",
        {
            "extracted_text": text,
            "document_info": metadata,
        },
    )


@require_http_methods(["GET"])
def keywords_view(request):
    session_id = request.session.get("active_document_chat_session_id")
    text = request.session.get("active_document_text")
    metadata = request.session.get("active_document_metadata")
    
    if not session_id or not text:
        return render(request, "core/keywords.html", {"no_document": True})
        
    try:
        keywords = extract_keywords(text, top_n=20)
        context = {"keywords": keywords, "document_info": metadata}
        messages.success(request, "Keywords extracted successfully.")
    except (ExtractionError, KeywordError) as exc:
        messages.error(request, str(exc))
        context = {"document_info": metadata}
    except Exception as exc:
        messages.error(request, f"Unexpected error: {exc}")
        context = {"document_info": metadata}
        
    return render(request, "core/keywords.html", context)


@require_http_methods(["GET", "POST"])
def quiz_view(request):
    session_id = request.session.get("active_document_chat_session_id")
    text = request.session.get("active_document_text")
    metadata = request.session.get("active_document_metadata")
    
    if not session_id or not text:
        return render(request, "core/quiz.html", {"no_document": True})
        
    questions = request.session.get("quiz_questions", [])
    if not questions:
        try:
            questions = generate_quiz(text)
            request.session["quiz_questions"] = questions
            messages.success(request, "Quiz generated successfully.")
        except (ExtractionError, QuizError) as exc:
            messages.error(request, str(exc))
            return render(request, "core/quiz.html", {"document_info": metadata, "error": str(exc)})
        except Exception as exc:
            messages.error(request, f"Unexpected error: {exc}")
            return render(request, "core/quiz.html", {"document_info": metadata, "error": str(exc)})
            
    context = {"questions": questions, "document_info": metadata}
    
    if request.method == "POST":
        answers = {key.replace("answer_", ""): value for key, value in request.POST.items() if key.startswith("answer_")}
        context.update({"score": score_quiz(questions, answers), "submitted_answers": answers})
        
    return render(request, "core/quiz.html", context)


def download_txt(request):
    content = request.session.get("download_text", "")
    filename = request.session.get("download_filename", "parikshon-ai-output.txt")
    if not content:
        messages.error(request, "There is no downloadable text available yet.")
        return redirect("core:home")
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
