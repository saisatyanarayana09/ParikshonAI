from django.urls import path

from . import auth_views, views, utility_views, seo_views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("robots.txt", seo_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", seo_views.sitemap_xml, name="sitemap_xml"),
    path("chat/", views.chat_view, name="chat"),
    path("ocr/", views.ocr_view, name="ocr"),
    path("keywords/", views.keywords_view, name="keywords"),
    path("quiz/", views.quiz_view, name="quiz"),

    # PDF Utilities
    path("utilities/merge/", utility_views.merge_view, name="merge_pdf"),
    path("utilities/split/", utility_views.split_view, name="split_pdf"),
    path("utilities/protect/", utility_views.protect_view, name="protect_pdf"),
    path("utilities/unlock/", utility_views.unlock_view, name="unlock_pdf"),
    path("utilities/rotate/", utility_views.rotate_view, name="rotate_pdf"),
    path("utilities/remove-pages/", utility_views.remove_pages_view, name="remove_pages"),
    path("utilities/jpg-to-pdf/", utility_views.jpg_to_pdf_view, name="jpg_to_pdf"),
    path("utilities/pdf-to-jpg/", utility_views.pdf_to_jpg_view, name="pdf_to_jpg"),
    path("utilities/pdf-to-text/", utility_views.pdf_to_text_view, name="pdf_to_text"),
    path("utilities/watermark/", utility_views.watermark_view, name="watermark_pdf"),
    path("utilities/page-numbers/", utility_views.add_page_numbers_view, name="page_numbers"),
    path("utilities/compress/", utility_views.compress_view, name="compress_pdf"),

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
