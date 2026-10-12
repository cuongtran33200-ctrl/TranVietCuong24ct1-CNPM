from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RegisterForm


class RegisterFormTests(TestCase):
    def test_duplicate_username_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username="cuong",
            email="cuong@example.com",
            password="ValidPass123!",
        )
        form = RegisterForm(
            data={
                "username": "Cuong",
                "email": "other@example.com",
                "password1": "AnotherPass123!",
                "password2": "AnotherPass123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Tên đăng nhập này đã được sử dụng. Vui lòng chọn tên khác.",
            form.errors["username"],
        )

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username="cuong",
            email="cuong@example.com",
            password="ValidPass123!",
        )
        form = RegisterForm(
            data={
                "username": "another",
                "email": "CUONG@example.com",
                "password1": "AnotherPass123!",
                "password2": "AnotherPass123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Email này đã được sử dụng. Vui lòng nhập email khác.",
            form.errors["email"],
        )


class LoginViewTests(TestCase):
    def test_invalid_credentials_show_vietnamese_error(self):
        User.objects.create_user(
            username="cuong",
            email="cuong@example.com",
            password="ValidPass123!",
        )

        response = self.client.post(
            reverse("shop:login"),
            {"username": "cuong", "password": "wrong-password"},
        )

        self.assertContains(
            response, "Tên đăng nhập hoặc mật khẩu không đúng."
        )
