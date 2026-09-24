from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User

INPUT_CLASSES = "field-input"


class StyledFormMixin:
    """Aplica las clases de Tailwind del proyecto a cualquier formulario que la use,
    incluidos los de Django (AuthenticationForm, UserCreationForm) sin redeclarar sus campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {INPUT_CLASSES}".strip()


class RegisterForm(StyledFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class LoginForm(StyledFormMixin, AuthenticationForm):
    pass
