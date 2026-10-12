from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RegisterForm
from .models import Category


class RegisterFormTests(TestCase):
    def test_username_is_trimmed_before_validation(self):
        form = RegisterForm(
            data={
                "username": "  new_user  ",
                "email": "new@example.com",
                "password1": "StrongPass!938",
                "password2": "StrongPass!938",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["username"], "new_user")

    def test_successful_registration_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("shop:register"),
            {
                "username": "new_user",
                "email": "new@example.com",
                "password1": "StrongPass!938",
                "password2": "StrongPass!938",
            },
        )

        self.assertRedirects(response, reverse("shop:product_list"))
        user = User.objects.get(username="new_user")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_registration_view_shows_duplicate_username_error(self):
        User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="ValidPass123!",
        )

        response = self.client.post(
            reverse("shop:register"),
            {
                "username": "Existing",
                "email": "other@example.com",
                "password1": "StrongPass!938",
                "password2": "StrongPass!938",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Tên đăng nhập này đã được sử dụng. Vui lòng chọn tên khác.",
        )
        self.assertEqual(User.objects.filter(username__iexact="existing").count(), 1)

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


class ProductListTests(TestCase):
    def test_homepage_renders_category_sections(self):
        Category.objects.create(name="Điện thoại", slug="dien-thoai")

        response = self.client.get(reverse("shop:product_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tất cả sản phẩm")
        self.assertContains(response, "Danh Mục Phổ Biến")
        self.assertContains(response, "Điện thoại")
        self.assertContains(response, "shop/img/products/iphone16-pro.jpg")
        self.assertContains(response, "shop/img/categories/cat-dienthoai.jpg")

    def test_view_all_page_renders_product_listing(self):
        response = self.client.get(reverse("shop:product_list"), {"all": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tất cả sản phẩm")
        self.assertNotContains(response, "Danh Mục Phổ Biến")
