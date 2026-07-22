"""Authentication views: register, login, logout, history."""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm
from .models import ChatSession

ANON_CHAT_LIMIT = 5


# ── Register ──────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:chat")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()

        # Migrate any anonymous chat session to the new account
        session_key = request.session.session_key
        if session_key:
            ChatSession.objects.filter(
                session_key=session_key, user__isnull=True
            ).update(user=user, session_key=None)

        # Reset the anon counter
        request.session.pop("anon_chat_count", None)

        login(request, user)
        messages.success(request, f"Welcome to Parikshon AI, {user.username}! Your account is ready.")
        return redirect("core:chat")

    return render(request, "auth/register.html", {"form": form})


# ── Login ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:chat")

    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()

        # Migrate anonymous sessions to this user on login
        session_key = request.session.session_key
        if session_key:
            ChatSession.objects.filter(
                session_key=session_key, user__isnull=True
            ).update(user=user, session_key=None)

        request.session.pop("anon_chat_count", None)
        login(request, user)
        messages.success(request, f"Welcome back, {user.username}!")
        return redirect(request.GET.get("next") or "core:chat")

    return render(request, "auth/login.html", {"form": form})


# ── Logout ────────────────────────────────────────────────────────────────────

def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("core:chat")


# ── History (signed-in only) ──────────────────────────────────────────────────

@login_required(login_url="core:login")
def history_view(request):
    sessions = (
        ChatSession.objects.filter(user=request.user)
        .prefetch_related("messages")
        .order_by("-updated_at")
    )
    return render(request, "core/history.html", {"sessions": sessions})
