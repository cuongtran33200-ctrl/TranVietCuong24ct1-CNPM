from django.contrib.auth import views as auth_views
from django.urls import path

from . import admin_views, staff_views, views
from .forms import LoginForm

app_name = "shop"

urlpatterns = [
    # ---- Khách hàng: mua hàng ----
    path("", views.product_list, name="product_list"),
    path("danh-muc/<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    path("san-pham/<slug:slug>/", views.product_detail, name="product_detail"),
    path("san-pham/<slug:slug>/danh-gia/", views.add_review, name="add_review"),

    path("gio-hang/", views.cart_detail, name="cart_detail"),
    path("gio-hang/them/<int:product_id>/", views.cart_add, name="cart_add"),
    path("gio-hang/xoa/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("gio-hang/cap-nhat/<int:product_id>/", views.cart_update, name="cart_update"),

    path("thanh-toan/", views.checkout, name="checkout"),

    # ---- Khách hàng: đơn hàng & tài khoản ----
    path("don-hang/", views.order_history, name="order_history"),
    path("don-hang/<int:order_id>/", views.order_detail, name="order_detail"),
    path("ho-so/", views.profile_view, name="profile"),
    path("ho-tro/", views.support_create, name="support_list"),

    path("dang-ky/", views.register, name="register"),
    path(
        "dang-nhap/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=LoginForm,
        ),
        name="login",
    ),
    path("dang-xuat/", auth_views.LogoutView.as_view(next_page="shop:product_list"), name="logout"),

    # ---- Nhân viên ----
    path("nhan-vien/don-hang/", staff_views.order_list, name="staff_order_list"),
    path("nhan-vien/don-hang/<int:order_id>/", staff_views.order_detail, name="staff_order_detail"),
    path("nhan-vien/kho/", staff_views.inventory_list, name="staff_inventory"),
    path("nhan-vien/kho/cap-nhat/<int:product_id>/", staff_views.inventory_update, name="staff_inventory_update"),
    path("nhan-vien/khach-hang/", staff_views.customer_list, name="staff_customer_list"),
    path("nhan-vien/khach-hang/<int:user_id>/", staff_views.customer_detail, name="staff_customer_detail"),
    path("nhan-vien/ho-tro/", staff_views.support_list, name="staff_support_list"),
    path("nhan-vien/ho-tro/<int:request_id>/", staff_views.support_detail, name="staff_support_detail"),

    # ---- Quản trị (Admin) ----
    path("quan-tri/", admin_views.dashboard, name="admin_dashboard"),
    path("quan-tri/nguoi-dung/", admin_views.user_list, name="admin_user_list"),
    path("quan-tri/nguoi-dung/<int:user_id>/vai-tro/", admin_views.user_set_role, name="admin_user_set_role"),
    path("quan-tri/thong-ke/doanh-thu/", admin_views.stats_revenue, name="admin_stats_revenue"),
    path("quan-tri/thong-ke/san-pham/", admin_views.stats_products, name="admin_stats_products"),
    path("quan-tri/thong-ke/khach-hang/", admin_views.stats_customers, name="admin_stats_customers"),
]
