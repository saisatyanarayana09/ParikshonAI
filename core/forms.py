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
    name = forms.CharField(
        label="Name",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Your Name", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "Email ID", "autocomplete": "email"}),
    )
    dob = forms.DateField(
        label="Date of Birth",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "placeholder": "Date of Birth"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Create a password", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat password", "autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1", "")
        p2 = cleaned.get("password2", "")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        
        if p1:
            if len(p1) < 8:
                self.add_error("password1", "Password must be at least 8 characters long.")
            if not any(char.isalpha() for char in p1):
                self.add_error("password1", "Password must contain at least one text character.")
            if not any(char.isdigit() for char in p1):
                self.add_error("password1", "Password must contain at least one number.")
            import string
            if not any(char in string.punctuation for char in p1):
                self.add_error("password1", "Password must contain at least one special symbol.")
        return cleaned

    def save(self):
        import uuid
        from .models import UserProfile
        data = self.cleaned_data
        base_username = data["email"].split("@")[0][:140]
        username = f"{base_username}_{uuid.uuid4().hex[:4]}"
        user = User.objects.create_user(
            username=username,
            email=data["email"],
            password=data["password1"],
            first_name=data["name"]
        )
        UserProfile.objects.create(user=user, dob=data.get("dob"))
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email ID",
        widget=forms.EmailInput(attrs={"placeholder": "Email ID", "autocomplete": "email"}),
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
        email = cleaned.get("email", "").strip()
        password = cleaned.get("password", "")
        if email and password:
            self._user = authenticate(self.request, email=email, password=password)
            if self._user is None:
                raise forms.ValidationError("Invalid email ID or password.")
        return cleaned

    def get_user(self):
        return self._user

