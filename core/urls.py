from django.urls import path

from . import auth_views, views

app_name = "core"

urlpatterns = [
    # Core workspace tools
    path("", views.home, name="home"),
    path("chat/", views.chat_view, name="chat"),
    path("ocr/", views.ocr_view, name="ocr"),
    path("keywords/", views.keywords_view, name="keywords"),
    path("quiz/", views.quiz_view, name="quiz"),

    # Document management
    path("upload/", views.global_upload_view, name="global_upload"),
    path("clear/", views.clear_document_view, name="clear_document"),
    path("download/txt/", views.download_txt, name="download_txt"),

    # Authentication
    path("register/", auth_views.register_view, name="register"),
    path("login/", auth_views.login_view, name="login"),
    path("logout/", auth_views.logout_view, name="logout"),

    # History (signed-in users)
    path("history/", auth_views.history_view, name="history"),
]
