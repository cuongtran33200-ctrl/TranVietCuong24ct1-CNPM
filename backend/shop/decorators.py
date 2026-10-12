from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        profile = request.user.profile
        if not profile.is_staff_role:
            messages.error(request, "Bạn không có quyền truy cập trang này.")
            return redirect("shop:product_list")
        return view_func(request, *args, **kwargs)
    return _wrapped


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        profile = request.user.profile
        if not profile.is_admin_role:
            messages.error(request, "Chỉ quản trị viên mới có quyền truy cập trang này.")
            return redirect("shop:product_list")
        return view_func(request, *args, **kwargs)
    return _wrapped
