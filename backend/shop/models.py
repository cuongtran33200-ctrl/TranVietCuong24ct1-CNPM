from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from cloudinary.models import CloudinaryField


class Profile(models.Model):
    ROLE_CUSTOMER = "customer"
    ROLE_STAFF = "staff"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, "Khách hàng"),
        (ROLE_STAFF, "Nhân viên"),
        (ROLE_ADMIN, "Quản trị viên"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    role = models.CharField(
        "Vai trò",
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_CUSTOMER
    )
    phone = models.CharField(
        "Số điện thoại",
        max_length=20,
        blank=True
    )
    address = models.CharField(
        "Địa chỉ",
        max_length=255,
        blank=True
    )

    class Meta:
        verbose_name = "Hồ sơ người dùng"
        verbose_name_plural = "Hồ sơ người dùng"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_staff_role(self):
        return (
            self.role in (self.ROLE_STAFF, self.ROLE_ADMIN)
            or self.user.is_superuser
        )

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN or self.user.is_superuser


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={
                "role": (
                    Profile.ROLE_ADMIN
                    if instance.is_superuser
                    else Profile.ROLE_CUSTOMER
                )
            },
        )
    else:
        Profile.objects.get_or_create(user=instance)


class Category(models.Model):
    name = models.CharField("Tên danh mục", max_length=100)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "shop:product_list_by_category",
            args=[self.slug]
        )


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE,
        verbose_name="Danh mục",
    )

    name = models.CharField(
        "Tên sản phẩm",
        max_length=200
    )

    slug = models.SlugField(
        max_length=220,
        unique=True
    )

    description = models.TextField(
        "Mô tả",
        blank=True
    )

    image = CloudinaryField(
        "Hình ảnh",
        folder="shop-sbcb/products",
        blank=True,
        null=True
    )

    price = models.DecimalField(
        "Giá (đ)",
        max_digits=12,
        decimal_places=0
    )

    stock = models.PositiveIntegerField(
        "Tồn kho",
        default=0
    )

    low_stock_threshold = models.PositiveIntegerField(
        "Ngưỡng cảnh báo sắp hết",
        default=5
    )

    compare_price = models.DecimalField(
        "Giá gốc (trước giảm)",
        max_digits=12,
        decimal_places=0,
        blank=True,
        null=True,
        help_text="Để trống nếu sản phẩm không giảm giá",
    )

    is_active = models.BooleanField(
        "Đang bán",
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "shop:product_detail",
            args=[self.slug]
        )

    @property
    def image_url(self):
        if not self.image:
            return ""

        if getattr(settings, "CLOUDINARY_URL", None):
            return self.image.url

        image_name = str(self.image.public_id)
        image_path = settings.MEDIA_ROOT / f"{image_name}.jpg"
        if image_path.exists():
            return f"{settings.MEDIA_URL}{image_name}.jpg"
        return ""

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_threshold

    @property
    def average_rating(self):
        reviews = self.reviews.all()

        if not reviews:
            return None

        return round(
            sum(r.rating for r in reviews) / len(reviews),
            1
        )

    @property
    def discount_percent(self):
        if self.compare_price and self.compare_price > self.price:
            return round(
                (1 - (self.price / self.compare_price)) * 100
            )

        return 0


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_SHIPPING = "shipping"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Chờ xác nhận"),
        (STATUS_CONFIRMED, "Đã xác nhận"),
        (STATUS_SHIPPING, "Đang giao"),
        (STATUS_COMPLETED, "Hoàn tất"),
        (STATUS_CANCELLED, "Đã hủy"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.CASCADE,
        verbose_name="Khách hàng",
    )

    full_name = models.CharField(
        "Họ tên người nhận",
        max_length=150
    )

    phone = models.CharField(
        "Số điện thoại",
        max_length=20
    )

    address = models.CharField(
        "Địa chỉ giao hàng",
        max_length=255
    )

    note = models.TextField(
        "Ghi chú",
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Đơn #{self.id} - {self.full_name}"

    @property
    def total_price(self):
        return sum(
            item.subtotal
            for item in self.items.all()
        )

    @property
    def total_items(self):
        return sum(
            item.quantity
            for item in self.items.all()
        )


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        related_name="order_items",
        on_delete=models.PROTECT
    )

    price = models.DecimalField(
        "Đơn giá tại thời điểm mua",
        max_digits=12,
        decimal_places=0
    )

    quantity = models.PositiveIntegerField(
        "Số lượng",
        default=1
    )

    class Meta:
        verbose_name = "Sản phẩm trong đơn"
        verbose_name_plural = "Sản phẩm trong đơn"

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="reviews",
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reviews",
        on_delete=models.CASCADE
    )

    rating = models.PositiveSmallIntegerField(
        "Số sao (1-5)",
        default=5
    )

    comment = models.TextField(
        "Nhận xét",
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Đánh giá"
        verbose_name_plural = "Đánh giá"
        ordering = ["-created_at"]
        unique_together = ("product", "user")

    def __str__(self):
        return (
            f"{self.user.username} đánh giá "
            f"{self.product.name} ({self.rating}★)"
        )


class SupportRequest(models.Model):
    STATUS_OPEN = "open"
    STATUS_RESOLVED = "resolved"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Đang chờ xử lý"),
        (STATUS_RESOLVED, "Đã xử lý"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="support_requests",
        on_delete=models.CASCADE
    )

    subject = models.CharField(
        "Tiêu đề",
        max_length=200
    )

    message = models.TextField(
        "Nội dung"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN
    )

    staff_reply = models.TextField(
        "Phản hồi của nhân viên",
        blank=True
    )

    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="handled_requests",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Yêu cầu hỗ trợ"
        verbose_name_plural = "Yêu cầu hỗ trợ"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"[{self.get_status_display()}] "
            f"{self.subject} - {self.user.username}"
        )