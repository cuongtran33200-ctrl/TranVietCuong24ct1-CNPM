from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import staff_required
from .models import Order, Product, SupportRequest


@staff_required
def order_list(request):
    orders = Order.objects.all().select_related("user")
    status = request.GET.get("status")
    if status:
        orders = orders.filter(status=status)
    context = {
        "orders": orders,
        "status_choices": Order.STATUS_CHOICES,
        "current_status": status or "",
    }
    return render(request, "shop/staff/order_list.html", context)


@staff_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        new_status = request.POST.get("status")
        valid_statuses = dict(Order.STATUS_CHOICES)
        if new_status in valid_statuses:
            order.status = new_status
            order.save()
            messages.success(request, f"Đã cập nhật trạng thái đơn #{order.id} → {valid_statuses[new_status]}")
        return redirect("shop:staff_order_detail", order_id=order.id)
    return render(request, "shop/staff/order_detail.html", {"order": order, "status_choices": Order.STATUS_CHOICES})


@staff_required
def inventory_list(request):
    products = Product.objects.all().select_related("category")
    only_low = request.GET.get("low") == "1"
    if only_low:
        products = [p for p in products if p.is_low_stock or p.stock == 0]
    context = {"products": products, "only_low": only_low}
    return render(request, "shop/staff/inventory_list.html", context)


@require_POST
@staff_required
def inventory_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        new_stock = int(request.POST.get("stock", product.stock))
        product.stock = max(0, new_stock)
        product.save()
        messages.success(request, f"Đã cập nhật tồn kho \"{product.name}\" → {product.stock}")
    except ValueError:
        messages.error(request, "Giá trị tồn kho không hợp lệ.")
    return redirect("shop:staff_inventory")


@staff_required
def customer_list(request):
    customers = User.objects.filter(profile__role="customer").order_by("-date_joined")
    return render(request, "shop/staff/customer_list.html", {"customers": customers})


@staff_required
def customer_detail(request, user_id):
    customer = get_object_or_404(User, id=user_id)
    orders = Order.objects.filter(user=customer)
    return render(request, "shop/staff/customer_detail.html", {"customer": customer, "orders": orders})


@staff_required
def support_list(request):
    requests_qs = SupportRequest.objects.all().select_related("user")
    only_open = request.GET.get("open") == "1"
    if only_open:
        requests_qs = requests_qs.filter(status=SupportRequest.STATUS_OPEN)
    return render(request, "shop/staff/support_list.html", {"requests": requests_qs, "only_open": only_open})


@staff_required
def support_detail(request, request_id):
    support_req = get_object_or_404(SupportRequest, id=request_id)
    if request.method == "POST":
        support_req.staff_reply = request.POST.get("staff_reply", "")
        support_req.status = SupportRequest.STATUS_RESOLVED
        support_req.handled_by = request.user
        support_req.save()
        messages.success(request, "Đã gửi phản hồi cho khách hàng.")
        return redirect("shop:staff_support_list")
    return render(request, "shop/staff/support_detail.html", {"req": support_req})
