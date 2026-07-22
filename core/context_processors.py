from core.forms import UploadForm
from core.models import ChatSession


def active_document_context(request):
    active_doc = None
    session_id = request.session.get("active_document_chat_session_id")
    if session_id:
        active_doc = ChatSession.objects.filter(id=session_id).first()

    return {
        "active_document": active_doc,
        "active_document_metadata": request.session.get("active_document_metadata"),
        "global_upload_form": UploadForm(),
    }
