from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class UploadForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control upload-input",
                "accept": ".pdf,.docx,.pptx,.txt,.csv,.jpg,.jpeg,.png,.webp",
            }
        )
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        extension = Path(uploaded.name).suffix.lower()
        if extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            allowed = ", ".join(sorted(settings.ALLOWED_UPLOAD_EXTENSIONS))
            raise forms.ValidationError(f"Unsupported file type. Allowed types: {allowed}.")
        if uploaded.size > settings.MAX_UPLOAD_SIZE:
            raise forms.ValidationError("File size must be 10MB or smaller.")
        return uploaded




class ChatQuestionForm(forms.Form):
    session_id = forms.UUIDField(widget=forms.HiddenInput)
    question = forms.CharField(
        min_length=2,
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Ask a question about the uploaded document...",
            }
        ),
    )


class QuizAnswerForm(forms.Form):
    answers = forms.JSONField()


# ── Authentication Forms ──────────────────────────────────────────────────────

class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Choose a username", "autocomplete": "username"}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "Email (optional)", "autocomplete": "email"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Create a password", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat password", "autocomplete": "new-password"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1", "")
        p2 = cleaned.get("password2", "")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        if p1:
            try:
                validate_password(p1)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self):
        data = self.cleaned_data
        return User.objects.create_user(
            username=data["username"],
            email=data.get("email", ""),
            password=data["password1"],
        )


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Username", "autocomplete": "username"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password", "autocomplete": "current-password"}),
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self._user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username", "").strip()
        password = cleaned.get("password", "")
        if username and password:
            self._user = authenticate(self.request, username=username, password=password)
            if self._user is None:
                raise forms.ValidationError("Invalid username or password.")
        return cleaned

    def get_user(self):
        return self._user

