from django.core.management.base import BaseCommand
from django.utils.text import slugify

from shop.models import Category, Product

CATEGORIES = ["Điện thoại", "Laptop", "Tai nghe", "Phụ kiện sạc", "Đồng hồ thông minh"]

# (category, name, price, compare_price hoặc None, stock, mô tả)
PRODUCTS = [
    ("Điện thoại", "iPhone 15 Pro Max 256GB", 32990000, 35990000, 15,
     "Chip A17 Pro, camera 48MP, khung titan cao cấp."),
    ("Điện thoại", "Samsung Galaxy S24 Ultra", 28990000, 32990000, 20,
     "Bút S Pen tích hợp, màn hình Dynamic AMOLED 2X."),
    ("Điện thoại", "Xiaomi 14T Pro", 14990000, None, 25,
     "Camera Leica, sạc nhanh 120W."),
    ("Laptop", "MacBook Air M3 13 inch", 27990000, None, 10,
     "Chip Apple M3, pin 18 giờ, siêu mỏng nhẹ."),
    ("Laptop", "Dell XPS 13", 24990000, 27490000, 8,
     "Màn hình InfinityEdge, thiết kế cao cấp."),
    ("Laptop", "Asus ROG Zephyrus G14", 34990000, 39990000, 6,
     "Laptop gaming mỏng nhẹ, RTX 4060."),
    ("Tai nghe", "AirPods Pro 2", 5990000, 6790000, 40,
     "Chống ồn chủ động, âm thanh không gian."),
    ("Tai nghe", "Sony WH-1000XM5", 7990000, None, 18,
     "Chống ồn hàng đầu thị trường, pin 30 giờ."),
    ("Phụ kiện sạc", "Sạc nhanh Anker 65W GaN", 890000, 1190000, 60,
     "Nhỏ gọn, sạc nhanh cho laptop và điện thoại."),
    ("Phụ kiện sạc", "Cáp USB-C to USB-C 100W", 250000, 350000, 100,
     "Dây bện cao cấp, hỗ trợ sạc nhanh 100W."),
    ("Đồng hồ thông minh", "Apple Watch Series 10", 10990000, None, 12,
     "Theo dõi sức khoẻ toàn diện, màn hình luôn sáng."),
    ("Đồng hồ thông minh", "Samsung Galaxy Watch 7", 7490000, 8490000, 14,
     "Đo điện tâm đồ, chống nước 5ATM."),
]


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu (danh mục + sản phẩm) cho shop SBCB"

    def handle(self, *args, **options):
        cat_map = {}
        for name in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=slugify(name), defaults={"name": name}
            )
            cat_map[name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f"+ Danh mục: {name}"))

        for cat_name, prod_name, price, compare_price, stock, desc in PRODUCTS:
            slug = slugify(prod_name)
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "category": cat_map[cat_name],
                    "name": prod_name,
                    "price": price,
                    "compare_price": compare_price,
                    "stock": stock,
                    "description": desc,
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  + Sản phẩm: {prod_name}"))
            else:
                product.compare_price = compare_price
                product.save(update_fields=["compare_price"])

        self.stdout.write(self.style.SUCCESS("Đã tạo xong dữ liệu mẫu cho SBCB!"))
