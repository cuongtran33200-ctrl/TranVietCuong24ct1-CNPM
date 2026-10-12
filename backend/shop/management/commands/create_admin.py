from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop.models import Profile


class Command(BaseCommand):
    help = "Tạo tài khoản admin cho Shop SBCB"

    def handle(self, *args, **options):
        User = get_user_model()

        username = "admin"
        email = "admin@shop-sbcb.com"
        password = "Admin@123456"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            }
        )

        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = Profile.ROLE_ADMIN
        profile.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Đã tạo/cập nhật tài khoản admin thành công!"
            )
        )