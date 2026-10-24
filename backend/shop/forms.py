from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Order, Profile, Review, SupportRequest

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Gmail / Email")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["username"].label = "Tên đăng nhập"
        self.fields["username"].widget.attrs.update(
            {
                "placeholder": "Nhập tên đăng nhập",
                "autofocus": True,
                "autocomplete": "username",
                "maxlength": 150,
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "placeholder": "Nhập địa chỉ Gmail hoặc email",
                "autocomplete": "email",
                "inputmode": "email",
            }
        )
        self.fields["password1"].label = "Mật khẩu"
        self.fields["password1"].widget.attrs.update(
            {"placeholder": "Nhập mật khẩu (tối thiểu 6 ký tự)", "autocomplete": "new-password"}
        )
        self.fields["password2"].label = "Nhập lại mật khẩu"
        self.fields["password2"].widget.attrs.update(
            {"placeholder": "Nhập lại mật khẩu", "autocomplete": "new-password"}
        )
        self.fields["password1"].help_text = "Mật khẩu cần ít nhất 6 ký tự."

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Email này đã được sử dụng. Vui lòng nhập email khác."
            )
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if password:
            validate_password(password)
        return password



class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Email hoặc mật khẩu không đúng.",
        "inactive": "Tài khoản này hiện không hoạt động.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"] = forms.EmailField(
            label="Gmail / Email",
            widget=forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nhập địa chỉ Gmail hoặc email",
                    "autocomplete": "email",
                    "inputmode": "email",
                    "autofocus": True,
                }
            ),
        )
        self.fields["password"].label = "Mật khẩu"
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Nhập mật khẩu"}
        )

    def clean_username(self):
        email = self.cleaned_data["username"].strip()
        user_model = get_user_model()
        try:
            user = user_model._default_manager.get(email__iexact=email)
        except user_model.DoesNotExist:
            raise forms.ValidationError(self.error_messages["invalid_login"])
        except user_model.MultipleObjectsReturned:
            raise forms.ValidationError(self.error_messages["invalid_login"])
        return user.get_username()


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1, initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "style": "width:90px"}),
    )


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["full_name", "phone", "address", "note"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Họ và tên"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Số điện thoại"}),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": "Địa chỉ giao hàng"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Ghi chú (tuỳ chọn)"}),
        }


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Họ tên", max_length=150, required=False,
                                  widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(label="Email", required=False,
                              widget=forms.EmailInput(attrs={"class": "form-control"}))

    class Meta:
        model = Profile
        fields = ["phone", "address"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
        }


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(i, f"{i} sao") for i in range(1, 6)],
        coerce=int,
        label="Số sao (1-5)",
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(attrs={"class": "form-select"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Chia sẻ cảm nhận của bạn..."}),
        }


class SupportRequestForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = ["subject", "message"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tiêu đề yêu cầu"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Mô tả vấn đề bạn gặp phải..."}),
        }
