from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RegisterForm
from .models import Category, Order, OrderItem, Product, Profile, Review, SupportRequest

CHECKOUT_DATA = {
    "full_name": "Khách Test",
    "phone": "0900000000",
    "address": "1 Test Street",
    "note": "",
}


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="ValidPass123!"
        )
        self.client.force_login(self.user)
        category = Category.objects.create(name="Điện thoại", slug="dien-thoai")
        self.product = Product.objects.create(
            category=category,
            name="iPhone Test",
            slug="iphone-test",
            price=1000,
            stock=3,
        )

    def _add_to_cart(self, quantity):
        self.client.post(
            reverse("shop:cart_add", args=[self.product.id]),
            {"quantity": quantity},
        )

    def test_successful_checkout_reduces_stock_and_uses_db_price(self):
        self._add_to_cart(2)
        # Giá trong session cũ bị giả mạo không được ảnh hưởng đến đơn hàng.
        session = self.client.session
        session["cart"][str(self.product.id)]["price"] = "1"
        session.save()

        response = self.client.post(reverse("shop:checkout"), CHECKOUT_DATA)

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        item = OrderItem.objects.get()
        self.assertEqual(item.price, 1000)
        self.assertEqual(item.quantity, 2)

    def test_checkout_rejects_quantity_above_stock(self):
        self._add_to_cart(5)

        response = self.client.post(reverse("shop:checkout"), CHECKOUT_DATA, follow=True)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertFalse(Order.objects.exists())
        self.assertContains(response, "chỉ còn 3 sản phẩm trong kho")

    def test_checkout_rejects_inactive_product(self):
        self._add_to_cart(1)
        self.product.is_active = False
        self.product.save()

        response = self.client.post(reverse("shop:checkout"), CHECKOUT_DATA, follow=True)

        self.assertFalse(Order.objects.exists())
        self.assertContains(response, "không còn được bán")


class PermissionTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer", email="c@example.com", password="ValidPass123!"
        )
        self.other_customer = User.objects.create_user(
            username="other", email="o@example.com", password="ValidPass123!"
        )
        self.staff = User.objects.create_user(
            username="staffer", email="s@example.com", password="ValidPass123!"
        )
        self.staff.profile.role = Profile.ROLE_STAFF
        self.staff.profile.save()
        self.admin = User.objects.create_user(
            username="boss", email="a@example.com", password="ValidPass123!"
        )
        self.admin.profile.role = Profile.ROLE_ADMIN
        self.admin.profile.save()

        category = Category.objects.create(name="Laptop", slug="laptop")
        self.product = Product.objects.create(
            category=category, name="Test Laptop", slug="test-laptop", price=500, stock=4
        )
        self.order = Order.objects.create(
            user=self.other_customer,
            full_name="Khách khác",
            phone="0911111111",
            address="2 Test Street",
        )

    def test_anonymous_user_is_sent_to_shop_login_for_staff_page(self):
        response = self.client.get(reverse("shop:staff_order_list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("shop:login"), response["Location"])

    def test_customer_cannot_open_staff_or_admin_pages(self):
        self.client.force_login(self.customer)

        for name in ("shop:staff_order_list", "shop:staff_inventory", "shop:admin_dashboard"):
            with self.subTest(url=name):
                response = self.client.get(reverse(name))
                self.assertRedirects(
                    response, reverse("shop:product_list"), fetch_redirect_response=False
                )

    def test_staff_can_open_staff_pages_but_not_admin_pages(self):
        self.client.force_login(self.staff)

        self.assertEqual(self.client.get(reverse("shop:staff_order_list")).status_code, 200)
        response = self.client.get(reverse("shop:admin_dashboard"))
        self.assertRedirects(
            response, reverse("shop:product_list"), fetch_redirect_response=False
        )

    def test_admin_can_open_admin_dashboard(self):
        self.client.force_login(self.admin)

        self.assertEqual(self.client.get(reverse("shop:admin_dashboard")).status_code, 200)

    def test_customer_cannot_view_another_customers_order(self):
        self.client.force_login(self.customer)

        response = self.client.get(reverse("shop:order_detail", args=[self.order.id]))

        self.assertEqual(response.status_code, 404)

    def test_customer_cannot_change_roles(self):
        self.client.force_login(self.customer)

        self.client.post(
            reverse("shop:admin_user_set_role", args=[self.customer.id]),
            {"role": Profile.ROLE_ADMIN},
        )

        self.customer.profile.refresh_from_db()
        self.assertEqual(self.customer.profile.role, Profile.ROLE_CUSTOMER)

    def test_customer_cannot_update_inventory(self):
        self.client.force_login(self.customer)

        self.client.post(
            reverse("shop:staff_inventory_update", args=[self.product.id]),
            {"stock": 999},
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)

    def test_staff_can_update_order_status(self):
        self.client.force_login(self.staff)

        self.client.post(
            reverse("shop:staff_order_detail", args=[self.order.id]),
            {"status": Order.STATUS_CONFIRMED},
        )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_CONFIRMED)


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


class CartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Tai nghe", slug="tai-nghe")
        self.product = Product.objects.create(
            category=category, name="Sony Test", slug="sony-test", price=300, stock=5
        )

    def test_add_product_to_cart_accumulates_quantity(self):
        self.client.post(reverse("shop:cart_add", args=[self.product.id]), {"quantity": 2})
        self.client.post(reverse("shop:cart_add", args=[self.product.id]), {"quantity": 1})

        self.assertEqual(self.client.session["cart"][str(self.product.id)]["quantity"], 3)

    def test_update_quantity_overrides_previous_value(self):
        self.client.post(reverse("shop:cart_add", args=[self.product.id]), {"quantity": 2})
        self.client.post(reverse("shop:cart_update", args=[self.product.id]), {"quantity": 4})

        self.assertEqual(self.client.session["cart"][str(self.product.id)]["quantity"], 4)

    def test_update_quantity_zero_removes_item(self):
        self.client.post(reverse("shop:cart_add", args=[self.product.id]), {"quantity": 2})
        self.client.post(reverse("shop:cart_update", args=[self.product.id]), {"quantity": 0})

        self.assertNotIn(str(self.product.id), self.client.session["cart"])

    def test_remove_product_from_cart(self):
        self.client.post(reverse("shop:cart_add", args=[self.product.id]), {"quantity": 1})
        self.client.post(reverse("shop:cart_remove", args=[self.product.id]))

        self.assertNotIn(str(self.product.id), self.client.session["cart"])

    def test_cart_add_rejects_get_requests(self):
        response = self.client.get(reverse("shop:cart_add", args=[self.product.id]))

        self.assertEqual(response.status_code, 405)


class ReviewTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username="buyer2", email="b2@example.com", password="ValidPass123!"
        )
        self.stranger = User.objects.create_user(
            username="stranger", email="s@example.com", password="ValidPass123!"
        )
        category = Category.objects.create(name="Laptop 2", slug="laptop-2")
        self.product = Product.objects.create(
            category=category, name="Asus Test", slug="asus-test", price=900, stock=5
        )
        order = Order.objects.create(
            user=self.buyer, full_name="Buyer", phone="0922222222", address="3 Street"
        )
        OrderItem.objects.create(order=order, product=self.product, price=900, quantity=1)

    def _review_url(self):
        return reverse("shop:add_review", args=[self.product.slug])

    def test_buyer_can_review_only_once(self):
        self.client.force_login(self.buyer)

        self.client.post(self._review_url(), {"rating": 5, "comment": "Tốt"})
        self.client.post(self._review_url(), {"rating": 1, "comment": "Thử lại"})

        reviews = Review.objects.filter(product=self.product, user=self.buyer)
        self.assertEqual(reviews.count(), 1)
        self.assertEqual(reviews.get().rating, 5)

    def test_user_without_purchase_cannot_review(self):
        self.client.force_login(self.stranger)

        self.client.post(self._review_url(), {"rating": 5, "comment": "Không mua"})

        self.assertFalse(Review.objects.filter(user=self.stranger).exists())

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.post(self._review_url(), {"rating": 5})

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("shop:login"), response["Location"])

    def test_invalid_rating_is_not_saved(self):
        self.client.force_login(self.buyer)

        self.client.post(self._review_url(), {"rating": 9, "comment": "Sai"})

        self.assertFalse(Review.objects.filter(user=self.buyer).exists())


class SupportAndOrderHistoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="helpme", email="h@example.com", password="ValidPass123!"
        )
        self.other = User.objects.create_user(
            username="other3", email="o3@example.com", password="ValidPass123!"
        )

    def test_customer_can_create_support_request(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("shop:support_list"),
            {"subject": "Lỗi sạc", "message": "Sạc không vào điện"},
        )

        request = SupportRequest.objects.get()
        self.assertEqual(request.user, self.user)
        self.assertEqual(request.status, SupportRequest.STATUS_OPEN)

    def test_support_page_lists_only_own_requests(self):
        SupportRequest.objects.create(user=self.other, subject="Của người khác", message="x")
        SupportRequest.objects.create(user=self.user, subject="Của tôi", message="y")
        self.client.force_login(self.user)

        response = self.client.get(reverse("shop:support_list"))

        self.assertContains(response, "Của tôi")
        self.assertNotContains(response, "Của người khác")

    def test_order_history_shows_only_own_orders(self):
        Order.objects.create(
            user=self.other, full_name="Người khác", phone="0933333333", address="4 Street"
        )
        Order.objects.create(
            user=self.user, full_name="Tôi", phone="0944444444", address="5 Street"
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("shop:order_history"))

        self.assertEqual(len(response.context["orders"]), 1)
        self.assertEqual(response.context["orders"][0].user, self.user)

