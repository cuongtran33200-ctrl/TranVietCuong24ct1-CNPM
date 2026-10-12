import base64
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import AddToCartForm, CheckoutForm, ProfileForm, RegisterForm, ReviewForm, SupportRequestForm
from .models import Category, Order, OrderItem, Product, Review, SupportRequest


def build_qr_data_uri(amount, order_id=None):
    order_label = f"DON HANG #{order_id}" if order_id else "DON HANG MOI"
    qr_content = f"SBCB SHOP | {order_label} | SO TIEN {amount:.0f} VND"
    qr_image = qrcode.make(qr_content)
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def product_list(request, category_slug=None):
    category = None
    image_products = Product.objects.filter(
        is_active=True,
        image__isnull=False,
    ).exclude(image="")
    categories = Category.objects.prefetch_related(
        Prefetch(
            "products",
            queryset=image_products.order_by("-created_at"),
            to_attr="image_products",
        )
    )
    categories = list(categories)
    products = Product.objects.filter(is_active=True)
    featured_image_product = image_products.order_by("-created_at").first()
    all_products_image = (
        featured_image_product.image_url
        if featured_image_product
        else static("shop/img/products/iphone16-pro.jpg")
    )
    category_image_fallbacks = (
        ("samsung", "shop/img/categories/cat-samsung.jpg"),
        ("thoại", "shop/img/categories/cat-dienthoai.jpg"),
        ("thoai", "shop/img/categories/cat-dienthoai.jpg"),
        ("phone", "shop/img/categories/cat-dienthoai.jpg"),
        ("laptop", "shop/img/categories/cat-laptop.webp"),
        ("tai nghe", "shop/img/products/sony-headphone.jpg"),
        ("headphone", "shop/img/products/sony-headphone.jpg"),
        ("nghe", "shop/img/products/sony-headphone.jpg"),
        ("sạc", "shop/img/categories/cat-sac.webp"),
        ("sac", "shop/img/categories/cat-sac.webp"),
        ("đồng hồ", "shop/img/categories/cat-dongho.webp"),
        ("dong ho", "shop/img/categories/cat-dongho.webp"),
        ("watch", "shop/img/categories/cat-dongho.webp"),
    )
    for item in categories:
        category_name = item.name.casefold()
        category_image = (
            item.image_products[0].image_url if item.image_products else ""
        )
        if not category_image:
            fallback_path = next(
                (
                    path
                    for keyword, path in category_image_fallbacks
                    if keyword in category_name
                ),
                None,
            )
            category_image = (
                static(fallback_path) if fallback_path else all_products_image
            )
        item.display_image = category_image

    apple_image_product = image_products.filter(
        Q(name__icontains="Apple")
        | Q(name__icontains="iPhone")
        | Q(name__icontains="MacBook")
        | Q(name__icontains="iPad")
    ).first()
    samsung_image_product = image_products.filter(
        Q(name__icontains="Samsung") | Q(name__icontains="Galaxy")
    ).first()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get("q", "").strip()
    show_all = request.GET.get("all") == "1"
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(slug__icontains=query)
        ).distinct()

    context = {
        "category": category,
        "categories": categories,
        "products": products,
        "query": query or "",
        "show_all": show_all,
        "all_products_image": all_products_image,
        "apple_image": (
            apple_image_product.image_url
            if apple_image_product
            else static("shop/img/products/iphone16-pro.jpg")
        ),
        "samsung_image": (
            samsung_image_product.image_url
            if samsung_image_product
            else static("shop/img/categories/cat-samsung.jpg")
        ),
    }
    return render(request, "shop/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    form = AddToCartForm()
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)[:4]

    review_form = None
    user_can_review = False
    if request.user.is_authenticated:
        already_reviewed = Review.objects.filter(product=product, user=request.user).exists()
        has_purchased = OrderItem.objects.filter(order__user=request.user, product=product).exists()
        user_can_review = has_purchased and not already_reviewed
        if user_can_review:
            review_form = ReviewForm()

    context = {
        "product": product,
        "form": form,
        "related_products": related_products,
        "reviews": product.reviews.all().select_related("user"),
        "review_form": review_form,
        "user_can_review": user_can_review,
    }
    return render(request, "shop/product_detail.html", context)


@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    has_purchased = OrderItem.objects.filter(order__user=request.user, product=product).exists()
    if not has_purchased:
        messages.error(request, "Bạn cần mua sản phẩm này trước khi đánh giá.")
        return redirect(product.get_absolute_url())
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, "Bạn đã đánh giá sản phẩm này rồi.")
        return redirect(product.get_absolute_url())

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Cảm ơn bạn đã đánh giá sản phẩm!", extra_tags="confetti")
    return redirect(product.get_absolute_url())


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = AddToCartForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd["quantity"])
        messages.success(request, f"Đã thêm \"{product.name}\" vào giỏ hàng.")
    return redirect("shop:cart_detail")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"Đã xoá \"{product.name}\" khỏi giỏ hàng.")
    return redirect("shop:cart_detail")


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 1
    if quantity < 1:
        cart.remove(product)
    else:
        cart.add(product=product, quantity=quantity, override_quantity=True)
    return redirect("shop:cart_detail")


def cart_detail(request):
    cart = Cart(request)
    return render(request, "shop/cart_detail.html", {"cart": cart})


@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Giỏ hàng của bạn đang trống.")
        return redirect("shop:product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.save()
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item["product"],
                        price=item["price"],
                        quantity=item["quantity"],
                    )
            cart.clear()
            messages.success(
                request,
                "Đặt hàng thành công! Cảm ơn bạn đã mua sắm tại SBCB.",
                extra_tags="confetti",
            )
            return redirect("shop:order_detail", order_id=order.id)
    else:
        initial = {}
        if request.user.first_name:
            initial["full_name"] = request.user.first_name
        form = CheckoutForm(initial=initial)

    return render(request, "shop/checkout.html", {
        "cart": cart,
        "form": form,
        "qr_code": build_qr_data_uri(cart.get_total_price()),
    })


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, "shop/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "shop/order_detail.html", {
        "order": order,
        "qr_code": build_qr_data_uri(order.total_price, order.id),
    })


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
            except IntegrityError:
                form.add_error(
                    None,
                    "Tên đăng nhập hoặc email vừa được đăng ký. "
                    "Vui lòng kiểm tra lại thông tin.",
                )
            else:
                login(request, user)
                messages.success(request, f"Chào mừng {user.username} đến với SBCB!")
                return redirect("shop:product_list")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.email = form.cleaned_data["email"]
            request.user.save()
            form.save()
            messages.success(request, "Đã cập nhật hồ sơ cá nhân.")
            return redirect("shop:profile")
    else:
        form = ProfileForm(
            instance=profile,
            initial={"first_name": request.user.first_name, "email": request.user.email},
        )
    return render(request, "shop/profile.html", {"form": form})


@login_required
def support_create(request):
    if request.method == "POST":
        form = SupportRequestForm(request.POST)
        if form.is_valid():
            support_req = form.save(commit=False)
            support_req.user = request.user
            support_req.save()
            messages.success(request, "Đã gửi yêu cầu hỗ trợ. Nhân viên sẽ phản hồi sớm nhất.")
            return redirect("shop:support_list")
    else:
        form = SupportRequestForm()
    my_requests = SupportRequest.objects.filter(user=request.user)
    return render(request, "shop/support.html", {"form": form, "my_requests": my_requests})
