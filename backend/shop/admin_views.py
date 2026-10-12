from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .models import Category, Order, OrderItem, Product, Profile


@admin_required
def dashboard(request):
    completed_orders = Order.objects.exclude(status=Order.STATUS_CANCELLED)
    total_revenue = sum(o.total_price for o in completed_orders)
    total_orders = Order.objects.count()
    total_customers = User.objects.filter(profile__role=Profile.ROLE_CUSTOMER).count()
    total_products = Product.objects.count()
    low_stock_count = sum(1 for p in Product.objects.all() if p.is_low_stock or p.stock == 0)

    top_products = (
        OrderItem.objects.values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    status_display = dict(Order.STATUS_CHOICES)
    orders_by_status = [
        {"status": row["status"], "count": row["count"], "label": status_display.get(row["status"], row["status"])}
        for row in Order.objects.values("status").annotate(count=Count("id"))
    ]

    context = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_products": total_products,
        "low_stock_count": low_stock_count,
        "top_products": top_products,
        "orders_by_status": orders_by_status,
    }
    return render(request, "shop/admin_panel/dashboard.html", context)


@admin_required
def user_list(request):
    users = User.objects.all().select_related("profile").order_by("-date_joined")
    return render(request, "shop/admin_panel/user_list.html", {"users": users, "roles": Profile.ROLE_CHOICES})


@require_POST
@admin_required
def user_set_role(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get("role")
    valid_roles = dict(Profile.ROLE_CHOICES)
    if new_role in valid_roles:
        target_user.profile.role = new_role
        target_user.profile.save()
        messages.success(request, f"Đã đổi vai trò của {target_user.username} → {valid_roles[new_role]}")
    return redirect("shop:admin_user_list")


@admin_required
def stats_revenue(request):
    orders = Order.objects.exclude(status=Order.STATUS_CANCELLED)
    total_revenue = sum(o.total_price for o in orders)
    return render(request, "shop/admin_panel/stats_revenue.html", {"orders": orders, "total_revenue": total_revenue})


@admin_required
def stats_products(request):
    top_products = (
        OrderItem.objects.values("product__id", "product__name")
        .annotate(total_sold=Sum("quantity"), revenue=Sum(F("quantity") * F("price")))
        .order_by("-total_sold")
    )
    low_stock_products = [p for p in Product.objects.all() if p.is_low_stock or p.stock == 0]
    return render(request, "shop/admin_panel/stats_products.html", {
        "top_products": top_products,
        "low_stock_products": low_stock_products,
    })


@admin_required
def stats_customers(request):
    customers = (
        User.objects.filter(profile__role=Profile.ROLE_CUSTOMER)
        .annotate(order_count=Count("orders"))
        .order_by("-order_count")
    )
    return render(request, "shop/admin_panel/stats_customers.html", {"customers": customers})
