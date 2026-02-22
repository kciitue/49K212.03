from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from .forms import *
# Create your views here.
@never_cache
@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if user.is_staff or user.is_superuser:
                    return redirect('home_admin')
                else:
                    return redirect('home_customer')
            else:
                messages.error(request, 'Tài khoản của bạn đã bị vô hiệu hóa!')
        else:
            messages.error(request, 'Sai tên đăng nhập hoặc mật khẩu!')
    return render(request, 'apartment/login.html')

def home_admin(request):
    context = {}
    return render(request, 'apartment/home_admin.html', context)

def home_customer(request):
    context = {}
    return render(request, 'apartment/home_customer.html', context)

def require_set_password_again(request):
    return render(request, 'apartment/forgot password/require_set_password_again.html')

def sent_email_noti(request):
    return  render(request, 'apartment/forgot password/password_reset_done.html')

def set_new_password(request):
    return render(request, 'apartment/forgot password/set_new_password.html')

def change_password_done(request):
    return render(request, 'apartment/forgot password/password_reset_complete.html')

def is_owner(user):
    return user.is_authenticated and user.is_superuser
@login_required
@user_passes_test(is_owner, login_url='login')
def user_management(request):
    users = User.objects.all().order_by('-date_joined')
    #Chức năng tìm kiếm
    search_query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    users = User.objects.all().order_by('-date_joined')
    status_filter = request.GET.get('status', '')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |  # Tìm trong tên
            Q(last_name__icontains=search_query) # Tìm trong họ & tên đệm
        )
    #Chức năng sort theo vai trò
    if role_filter == 'owner':
        users = users.filter(is_superuser=True) #Chủ trọ
    elif role_filter == 'renter':
        users = users.filter(is_superuser=False) #Người thuê
    #Chức năng sort theo trạng thái hoạt động
    if status_filter == 'active':
        users = users.filter(is_active=True) #Hoạt động
    elif status_filter == 'inactive':
        users = users.filter(is_active=False) #Không hoạt động
    #Chức năng phân trang
    paginator = Paginator(users, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'users': page_obj,
        'total_users': User.objects.count(),
        'owners':User.objects.filter(is_superuser=True).count(),
        'renters': User.objects.filter(is_superuser=False).count(),
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'apartment/user_management.html', context)


@login_required
@user_passes_test(is_owner, login_url='login')
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        is_active = request.POST.get('is_active') == 'on'
        is_owner = request.POST.get('is_owner') == 'on'

        # Validate dữ liệu
        if password != confirm_password:
            messages.error(request, "Mật khẩu xác nhận không khớp!")
            return redirect('add_user')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Tên đăng nhập đã tồn tại!")
            return redirect('add_user')
        try:
            # Lưu User mới
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            # Phân quyền
            if is_owner:
                user.is_superuser = True
                user.is_staff = True
            else:
                user.is_superuser = False
                user.is_staff = False
            user.save()
            messages.success(request, f"Đã thêm người dùng {last_name} {first_name} thành công!")
            return redirect('user_management')
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {e}")
            return redirect('add_user')
    return render(request, 'apartment/add_user.html')

#Xóa tài khoản
@login_required
@user_passes_test(is_owner, login_url='login')
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, pk=user_id)
    if request.user.id == user_to_delete.id:
        messages.error(request, "Lỗi: Bạn không thể tự xóa tài khoản của chính mình!")
    else:
        # Nếu không phải tự xóa, tiến hành xóa và thông báo
        full_name = f"{user_to_delete.last_name} {user_to_delete.first_name}".strip()
        username = user_to_delete.username  # Lưu lại tên để hiển thị thông báo
        user_to_delete.delete()
        messages.success(request, f"Đã xóa người dùng {full_name} thành công!")
    return redirect('user_management')

#Cập nhật tài khoản
def edit_user(request, user_id):
    user_to_edit =get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật thông tin người dùng thành công!')
            return redirect('user_management')
    else:
        #Mở form thì tự động điền sẵn các thông tin Họ, Tên và Email cũ
        form = UserUpdateForm(instance=user_to_edit)
    #Khi edit thì sẽ hiển thị dữ liệu cũ
    return render(request, 'apartment/add_user.html',{
    'form': form,
    'user_to_edit': user_to_edit,
    'is_edit': True
    })
#Tính năng bật/tắt tài khoản
@login_required
@user_passes_test(is_owner, login_url='login')
@require_POST
def toggle_user_status(request, user_id):
    try:
        # Lấy thông tin user cần đổi trạng thái
        user_to_toggle = User.objects.get(id=user_id)

        # Đọc dữ liệu JSON gửi từ Javascript
        data = json.loads(request.body)
        new_status = data.get('is_active')

        # Ngăn Chủ trọ tự khóa tài khoản của chính mình
        if request.user.id == user_to_toggle.id:
            return JsonResponse({'success': False, 'error': 'Bạn không thể tự khóa tài khoản của chính mình!'})

        # Cập nhật trạng thái
        user_to_toggle.is_active = new_status
        user_to_toggle.save()

        return JsonResponse({'success': True})

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy người dùng'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})