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
from .models import Room, Contract, ContractDocument, Invoice, UserProfile
from datetime import datetime, date
from django.core.mail import send_mail
from django.urls import reverse
import os
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from html2image import Html2Image
import re
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper, IntegerField
from django.utils import timezone
# Create your views here.

def logout_view(request):
    logout(request)
    messages.success(request, "Đăng xuất thành công!")
    return redirect('login')

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
    return render(request, 'app/login.html')

@login_required
@never_cache
def home_admin(request):
    rooms = Room.objects.filter(owner=request.user).order_by('floor')
    context = {'rooms': rooms}
    return render(request, 'app/home_admin.html', context)

@login_required
@never_cache
def home_customer(request):
    user_room = Room.objects.filter(contracts__renter=request.user).distinct().first()
    invoices = Invoice.objects.filter(renter=request.user).order_by('-billing_month')
    
    context = {
        'room': user_room,
        'invoices': invoices,
    }
    return render(request, 'app/home_customer.html', context)

def require_set_password_again(request):
    return render(request, 'app/forgot password/require_set_password_again.html')

def sent_email_noti(request):
    return  render(request, 'app/forgot password/password_reset_done.html')

def set_new_password(request):
    return render(request, 'app/forgot password/set_new_password.html')

def change_password_done(request):
    return render(request, 'app/forgot password/password_reset_complete.html')

def is_owner(user):
    return user.is_authenticated and user.is_superuser

@login_required
@never_cache
@user_passes_test(is_owner, login_url='login')
def user_management(request):
    users = User.objects.filter(Q(id=request.user.id) | Q(is_superuser=False, profile__owner=request.user)).order_by('-date_joined')
    #Chức năng tìm kiếm
    search_query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    # users = User.objects.all().order_by('-date_joined')
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
        'total_users': User.objects.filter(is_superuser=False, profile__owner=request.user).count()+1,
        # 'owners':User.objects.filter(is_superuser=True).count(),
        'owners':1,
        'renters': User.objects.filter(is_superuser=False, profile__owner = request.user).count(),
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'app/user_management.html', context)


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
            if not is_owner:
                UserProfile.objects.create(user = user, owner = request.user)
            messages.success(request, f"Đã thêm người dùng {last_name} {first_name} thành công!")
            return redirect('user_management')
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {e}")
            return redirect('add_user')
    return render(request, 'app/add_user.html')

#Xóa tài khoản
@login_required
@user_passes_test(is_owner, login_url='login')
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, Q(id=request.user.id) | Q(profile__owner=request.user), pk=user_id)
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
    user_to_edit = get_object_or_404(User, Q(id=request.user.id) | Q(profile__owner=request.user), pk=user_id)
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
    return render(request, 'app/add_user.html',{
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

#Thêm phòng và thông tin người thuê
def add_room(request):
    if request.method == 'POST':
        try:
            # 1. HÀM DỌN DẸP SỐ
            def to_int(value):
                if not value: return 0
                return int(str(value).replace('.', '').replace(',', '').strip())

            # 2. LẤY VÀ ĐỒNG BỘ THÔNG TIN PHÒNG
            name = request.POST.get('name', '').strip()
            if Room.objects.filter(owner = request.user, name=name).exists():
                messages.error(request, f"Lỗi: Phòng {name} đã tồn tại!")
                return redirect('add_room')
            floor = request.POST.get('floor', '1')
            area = float(request.POST.get('area') or 0)
            max_occupancy = to_int(request.POST.get('max_occupancy'))

            # ĐỒNG BỘ TRẠNG THÁI:
            status_map = {'available': 'Trống', 'rented': 'Đang thuê', 'maintenance': 'Sửa chữa','deposited': 'Đã cọc'}
            form_status = request.POST.get('status', 'available')
            status = status_map.get(form_status, 'Trống')

            # Áp dụng to_int cho TẤT CẢ các trường tiền tệ và chỉ số
            base_rent = to_int(request.POST.get('base_rent'))
            electricity_price = to_int(request.POST.get('electricity_price'))
            water_price = to_int(request.POST.get('water_price'))
            trash_price = to_int(request.POST.get('trash_price'))
            internet_price = to_int(request.POST.get('internet_price'))
            current_electricity = to_int(request.POST.get('current_electricity'))
            current_water = to_int(request.POST.get('current_water'))

            # Tiện nghi
            air_conditioner = request.POST.get('air_conditioner') == 'on'
            water_heater = request.POST.get('water_heater') == 'on'
            refrigerator = request.POST.get('refrigerator') == 'on'
            furniture = request.POST.get('furniture') == 'on'
            balcony = request.POST.get('balcony') == 'on'

            # TẠO PHÒNG MỚI
            room = Room.objects.create(
                owner = request.user,
                name=name, floor=floor, area=area, max_occupancy=max_occupancy,
                base_rent=base_rent, status=status,
                air_conditioner=air_conditioner, water_heater=water_heater,
                refrigerator=refrigerator, furniture=furniture,
                balcony=balcony,
                electricity_price=electricity_price, water_price=water_price,
                trash_price=trash_price, internet_price=internet_price,
                current_electricity=current_electricity,
                current_water=current_water
            )

            # 3. XỬ LÝ HỢP ĐỒNG (Nếu chọn trạng thái 'Đang thuê')
            if status in ['Đang thuê', 'Đã cọc']:
                start_date = request.POST.get('start_date')
                renter_id = request.POST.get('renter_id')

                if start_date and renter_id:
                    selected_user = User.objects.get(id=renter_id)
                    deposit = to_int(request.POST.get('deposit'))
                    duration = to_int(request.POST.get('duration'))
                    identify = request.POST.get('identify', '')
                    phone_number = request.POST.get('phone_number', '')

                    new_contract = Contract.objects.create(
                        room=room, renter=selected_user, start_date=start_date,
                        duration=duration, identify=identify, phone_number=phone_number,
                        deposit=deposit
                    )

                    # Lưu hình ảnh hợp đồng
                    files = request.FILES.getlist('document_file')
                    for f in files:
                        ContractDocument.objects.create(contract=new_contract, file=f)

            messages.success(request, f"Đã thêm phòng {name} thành công!")
            return redirect('home_admin')

        except Exception as e:
            
            print(f"LỖI THÊM PHÒNG: {e}")
            messages.error(request, f"Lỗi hệ thống: {e}")
            return redirect('add_room')

    # GET REQUEST
    users = User.objects.filter(is_staff=False, profile__owner = request.user)
    context = {'users': users}
    return render(request, 'app/add_room.html', context)

def delete_room(request, room_id):
    room = Room.objects.get(id=room_id)
    room.delete()
    messages.success(request, f"Đã xóa phòng {room.name} thành công!")
    return redirect('home_admin')


def edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    users = User.objects.filter(is_staff=False, profile__owner = request.user)

    if request.method == 'POST':
        try:
            def to_int(value):
                if not value: return 0
                return int(str(value).replace('.', '').replace(',', '').strip())

            new_name = request.POST.get('name', '').strip()
            if Room.objects.filter(owner = request.user, name=new_name).exclude(id=room_id).exists():
                messages.error(request, f"Lỗi: Không thể đổi số phòng thành '{new_name}' vì đã có phòng khác sử dụng!")
                return redirect('edit_room', room_id=room_id)
                
            room.name = new_name
            room.floor = request.POST.get('floor', '1')
            
            area_str = str(request.POST.get('area', '0')).replace(',', '.')
            room.area = float(area_str) if area_str else 0.0
            
            room.max_occupancy = to_int(request.POST.get('max_occupancy'))

            status_map = {'available': 'Trống', 'rented': 'Đang thuê', 'maintenance': 'Sửa chữa','deposited': 'Đã cọc' }
            form_status = request.POST.get('status', 'available')
            room.status = status_map.get(form_status, 'Trống')

            room.base_rent = to_int(request.POST.get('base_rent'))
            room.electricity_price = to_int(request.POST.get('electricity_price'))
            room.water_price = to_int(request.POST.get('water_price'))
            room.trash_price = to_int(request.POST.get('trash_price'))
            room.internet_price = to_int(request.POST.get('internet_price'))

            room.current_electricity = to_int(request.POST.get('current_electricity'))
            room.current_water = to_int(request.POST.get('current_water'))

            room.air_conditioner = request.POST.get('air_conditioner') == 'on'
            room.water_heater = request.POST.get('water_heater') == 'on'
            room.refrigerator = request.POST.get('refrigerator') == 'on'
            room.furniture = request.POST.get('furniture') == 'on'
            room.balcony = request.POST.get('balcony') == 'on'

            room.save()  

            if room.status in ['Đang thuê', 'Đã cọc']:
                start_date = request.POST.get('start_date')
                renter_id = request.POST.get('renter_id')

                if start_date and renter_id:
                    selected_user = User.objects.get(id=renter_id)
                    contract = room.active_contract

                    identify = request.POST.get('identify', '')
                    phone_number = request.POST.get('phone_number', '')
                    deposit = to_int(request.POST.get('deposit'))
                    duration = to_int(request.POST.get('duration'))

                    if contract:
                        contract.renter = selected_user
                        contract.start_date = start_date
                        contract.duration = duration
                        contract.deposit = deposit
                        contract.identify = identify
                        contract.phone_number = phone_number
                        contract.save()
                    else:
                        contract = Contract.objects.create(
                            room=room, renter=selected_user, start_date=start_date,
                            duration=duration, deposit=deposit, identify=identify,
                            phone_number=phone_number
                        )

                    delete_ids = request.POST.getlist('delete_documents')
                    if delete_ids:
                        ContractDocument.objects.filter(id__in=[did for did in delete_ids if did]).delete()

                    files = request.FILES.getlist('document_file')
                    for f in files:
                        ContractDocument.objects.create(contract=contract, file=f)

            messages.success(request, f"Đã cập nhật thông tin phòng {room.name} thành công!")
            return redirect('home_admin')

        except Exception as e:
            print(f"LỖI SỬA PHÒNG: {e}")
            return redirect('edit_room', room_id=room_id)

    return render(request, 'app/add_room.html', {'users': users, 'room': room})

#Thêm hóa đơn
def add_invoice(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    current_contract = room.active_contract
    if request.method == 'POST':
        # Xử lý ngày tháng
        raw_month = request.POST.get('billing_month')
        if raw_month:
            billing_date = f"{raw_month}-01" # Định dạng YYYY-MM-01
        else:
            # Nếu không chọn, mặc định lấy mùng 1 của tháng hiện tại
            billing_date = date.today().replace(day=1)
        if Invoice.objects.filter(room=room, billing_month=billing_date).exists():
            if isinstance(billing_date, str):
                display_month = datetime.strptime(billing_date, "%Y-%m-%d").strftime('%m/%Y')
            else:
                display_month = billing_date.strftime('%m/%Y')
                
            messages.error(request, f"Lỗi: Phòng {room.name} đã có hóa đơn cho tháng {display_month}!")
            return redirect('add_invoice', room_id=room.id)

        # Lấy dữ liệu
        new_elec = int(request.POST.get('new_electricity', 0))
        new_water = int(request.POST.get('new_water', 0))
        raw_extra_fee = request.POST.get('extra_fee', '').replace('.', '').strip()
        extra_fee = int(raw_extra_fee or '0')
        #extra_fee = int(request.POST.get('extra_fee', '0').replace('.', ''))
        reason = request.POST.get('extra_fee_reason', '')
        
        # Biến action sẽ nhận giá trị 'unpaid' (bấm nút Tạo hóa đơn) hoặc 'draft' (bấm nút Lưu nháp)
        action = request.POST.get('action')

        # Tính toán tiền bạc
        old_elec = room.current_electricity or 0
        old_water = room.current_water or 0
        
        elec_usage = max(0, new_elec - old_elec)
        water_usage = max(0, new_water - old_water)
        
        total = (room.base_rent + 
                 (elec_usage * room.electricity_price) + 
                 (water_usage * room.water_price) + 
                 room.trash_price + room.internet_price + extra_fee)

        # 1. LƯU BẢN NHÁP VÀO DATABASE
        # Sửa lỗi: Chỉ gán status='draft', xóa bỏ chữ status=action bị lặp lại
        new_invoice = Invoice.objects.create(
            room=room, 
            renter=current_contract.renter if current_contract else None,
            billing_month=billing_date, 
            status='draft', 
            base_rent=room.base_rent, electricity_price=room.electricity_price,
            water_price=room.water_price, trash_price=room.trash_price,
            internet_price=room.internet_price, old_electricity=old_elec,
            new_electricity=new_elec, old_water=old_water, new_water=new_water,
            extra_fee=extra_fee, extra_fee_reason=reason, total_amount=total
        )

        # 2. ĐIỀU CHỈNH LUỒNG CHUYỂN TRANG
        if action == 'unpaid':
            # Nếu bấm "Tạo hóa đơn" -> Chuyển sang trang Preview (hóa đơn vẫn đang là nháp)
            return redirect('invoice_detail', invoice_id=new_invoice.id)
        else:
            # Nếu bấm "Lưu nháp" -> Về trang chủ và hiện thông báo
            messages.success(request, "Đã lưu nháp hóa đơn thành công!")
            return redirect('home_admin')

    # Khi mở form lên (GET)
    context = {
        'room': room,
        'suggested_date': date.today().strftime('%Y-%m'),
    }
    return render(request, 'app/add_invoice.html', context)


#Chi tiết hóa đơn
@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    elec_usage = max(0, invoice.new_electricity - invoice.old_electricity)
    elec_total = elec_usage * invoice.electricity_price
    
    water_usage = max(0, invoice.new_water - invoice.old_water)
    water_total = water_usage * invoice.water_price
    
    service_total = invoice.trash_price + invoice.internet_price
    
    context = {
        'invoice': invoice,
        'elec_usage': elec_usage,
        'elec_total': elec_total,
        'water_usage': water_usage,
        'water_total': water_total,
        'service_total': service_total,
    }
    return render(request, 'app/invoice_detail.html', context)

@login_required
def confirm_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if invoice.status == 'draft':
        # 1. Đổi trạng thái thành chính thức
        invoice.status = 'unpaid'
        invoice.save()
        
        # 2. BÂY GIỜ MỚI CẬP NHẬT SỐ ĐIỆN NƯỚC VÀO PHÒNG
        room = invoice.room
        room.current_electricity = invoice.new_electricity
        room.current_water = invoice.new_water
        room.save()
        
        messages.success(request, "Hóa đơn đã được gửi và lưu thành công!")
    return redirect('home_admin')

@login_required
def cancel_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, room__owner = request.user)
    # Chỉ cho phép xóa nếu hóa đơn vẫn đang là nháp
    if invoice.status == 'draft':
        invoice.delete()
        messages.success(request, "Đã hủy hóa đơn!")    
    return redirect('invoice_management')

#Quản lý hóa đơn
@login_required
def invoice_management(request):
    invoices = Invoice.objects.filter(room__owner=request.user).order_by('-created_at')
    
    # 2. LẤY LUÔN DANH SÁCH PHÒNG CỦA CHỦ TRỌ ĐÓ (Để lát làm bộ lọc)
    rooms = Room.objects.filter(owner=request.user)
    
    context = {
        'invoices': invoices,
        'rooms': rooms, # Gửi danh sách phòng sang giao diện
    }
    return render(request, 'app/invoice_management.html', context)

#Chỉnh sửa hóa đơn
@login_required
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, room__owner=request.user)
    
    if request.method == 'POST':
        old_status = invoice.status
        new_status = request.POST.get('status')
        
        if new_status in ['draft', 'unpaid', 'paid']:
            invoice.status = new_status
            invoice.save()
            
            # LOGIC CHỐT SỐ: Nếu chuyển từ "Nháp" sang "Chốt" (Unpaid/Paid)
            # Cập nhật ngay chỉ số điện nước mới vào Phòng để kỳ sau tính tiếp
            if old_status == 'draft' and new_status in ['unpaid', 'paid']:
                room = invoice.room
                room.current_electricity = invoice.new_electricity
                room.current_water = invoice.new_water
                room.save()

            messages.success(request, f"Đã cập nhật trạng thái hóa đơn HD{invoice.id:04d} thành công!")
            return redirect('invoice_management')

    # TÍNH TOÁN DỮ LIỆU HIỂN THỊ (Chỉ xem, không sửa)
    elec_usage = max(0, invoice.new_electricity - invoice.old_electricity)
    elec_total = elec_usage * invoice.electricity_price
    water_usage = max(0, invoice.new_water - invoice.old_water)
    water_total = water_usage * invoice.water_price
    service_total = invoice.trash_price + invoice.internet_price
    
    context = {
        'invoice': invoice,
        'elec_usage': elec_usage,
        'elec_total': elec_total,
        'water_usage': water_usage,
        'water_total': water_total,
        'service_total': service_total,
    }
    return render(request, 'app/edit_invoice.html', context)

#Xem hóa đơn
def view_invoice(request, invoice_id):
    # BẢO MẬT: Chỉ lấy hóa đơn nếu phòng đó thuộc sở hữu của người đang đăng nhập
    # Nếu truy cập ID của người khác, sẽ trả về lỗi 404.
    invoice = get_object_or_404(Invoice, id=invoice_id, room__owner=request.user)
    
    # Tính toán các con số tiêu thụ để hiển thị
    elec_usage = max(0, invoice.new_electricity - invoice.old_electricity)
    elec_total = elec_usage * invoice.electricity_price
    
    water_usage = max(0, invoice.new_water - invoice.old_water)
    water_total = water_usage * invoice.water_price
    
    # Tổng tiền dịch vụ cố định (Rác + Internet)
    service_total = invoice.trash_price + invoice.internet_price
    
    context = {
        'invoice': invoice,
        'elec_usage': elec_usage,
        'elec_total': elec_total,
        'water_usage': water_usage,
        'water_total': water_total,
        'service_total': service_total,
    }
    return render(request, 'app/view_invoice.html', context)


def quick_invoice_search(request):
    if request.method == 'POST':
        search_query = request.POST.get('invoice_code', '').strip().upper()
        if search_query.startswith('HD'):
            try:
                invoice_id = int(search_query.replace('HD', ''))
                invoice = Invoice.objects.get(id=invoice_id)
                if invoice.status == 'draft':
                    messages.error(request, "Hóa đơn này đang là bản nháp, bạn chưa thể xem")
                    return redirect('login')
                return redirect('guest_invoice_detail', invoice_id=invoice.id)
                
            except (ValueError, Invoice.DoesNotExist):
                pass 
        messages.error(request, "Mã hóa đơn không đúng, vui lòng kiểm tra lại!")
    
    return redirect('login')

#Hàm khách xem hóa đơn nhanh
def guest_invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if invoice.status == 'draft':
        messages.error(request, "Bạn không có quyền xem hóa đơn này.")
        return redirect('login')

    # Tính toán số liệu
    elec_usage = max(0, invoice.new_electricity - invoice.old_electricity)
    elec_total = elec_usage * invoice.electricity_price
    water_usage = max(0, invoice.new_water - invoice.old_water)
    water_total = water_usage * invoice.water_price
    service_total = invoice.trash_price + invoice.internet_price
    
    context = {
        'invoice': invoice,
        'elec_usage': elec_usage,
        'elec_total': elec_total,
        'water_usage': water_usage,
        'water_total': water_total,
        'service_total': service_total,
    }
    
    return render(request, 'app/guest_invoice_detail.html', context)

@login_required
def confirm_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, room__owner=request.user)
    
    # 1. CHỐT SỐ LIỆU (Giữ nguyên)
    if invoice.status == 'draft':
        invoice.status = 'unpaid'
        invoice.save()
        
        room = invoice.room
        room.current_electricity = invoice.new_electricity
        room.current_water = invoice.new_water
        room.save()

    # 2. CHỤP ẢNH VÀ GỬI EMAIL
    if invoice.renter and invoice.renter.email:
        try:
            # --- A. Chuẩn bị dữ liệu HTML ---
            elec_usage = max(0, invoice.new_electricity - invoice.old_electricity)
            water_usage = max(0, invoice.new_water - invoice.old_water)
            
            context = {
                'invoice': invoice,
                'elec_usage': elec_usage,
                'elec_total': elec_usage * invoice.electricity_price,
                'water_usage': water_usage,
                'water_total': water_usage * invoice.water_price,
                'service_total': invoice.trash_price + invoice.internet_price,
                'request': request, # Cần thiết để HTML lấy được user
            }
            
            # Biến cái file giao diện của Khách thành một chuỗi chữ HTML
            html_string = render_to_string('app/invoice_email.html', context)

            # --- B. Chụp ảnh màn hình ---
            hti = Html2Image()
            img_filename = f"hoadon_{invoice.id:04d}.png"
            
            # Cấu hình kích thước ảnh (rộng 900px, cao tự động) và chụp
            hti.screenshot(html_str=html_string, save_as=img_filename, size=(900, 1100))
            
            # --- C. Đính kèm vào Email và gửi đi ---
            subject = f"Hóa đơn tiền phòng {invoice.room.name} - Tháng {invoice.billing_month.strftime('%m/%Y')}"
            body = f"Xin chào {invoice.renter.last_name} {invoice.renter.first_name},\nVui lòng xem hình ảnh hóa đơn chi tiết của bạn được đính kèm bên dưới.\nThanh toán bằng mã QR đính kèm trong hóa đơn hoặc chuyển khoản theo tài khoản ngân hàng dưới đây:\nNgân hàng: MB Bank\nSTK: 0889341777\nChủ tài khoản: BUI XUAN HUY\nMã tra cứu nhanh của bạn trên website là: HD{invoice.id:04d}\n\nCảm ơn bạn!"
            
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.EMAIL_HOST_USER,
                to=[invoice.renter.email],
            )
            
            # Đính kèm bức ảnh vừa chụp
            email.attach_file(img_filename)
            email.send(fail_silently=False)
            
            if os.path.exists(img_filename):
                os.remove(img_filename)
                
            messages.success(request, f"Đã lưu hóa đơn và gửi ảnh hóa đơn qua Email: {invoice.renter.email}!")
            
        except Exception as e:
            messages.warning(request, f"Đã lưu hóa đơn nhưng lỗi khi tạo/gửi ảnh: {e}")
    else:
        messages.success(request, "Đã lưu hóa đơn thành công!")

    return redirect('invoice_management')

@csrf_exempt
def sepay_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content', '').upper() # Lấy nội dung CK (VD: NGUYEN VAN A CHUYEN TIEN HD0030)
            amount = int(data.get('transferAmount', 0)) # Lấy số tiền

            # Tìm cụm "HD" kèm con số phía sau
            match = re.search(r'HD(\d+)', content)
            
            if match:
                invoice_id = int(match.group(1)) # Ép kiểu '0030' thành số 30
                try:
                    invoice = Invoice.objects.get(id=invoice_id)
                    
                    # Kiểm tra tiền gửi vào >= tổng tiền HĐ, và HĐ chưa thanh toán
                    if amount >= invoice.total_amount and invoice.status != 'paid':
                        invoice.status = 'paid'
                        invoice.save()
                        print(f"Đã thanh toán thành công cho Hóa đơn HD{invoice_id:04d}")
                        return JsonResponse({'success': True, 'message': 'Thanh toán thành công'})
                        
                except Invoice.DoesNotExist:
                    pass # Không tìm thấy HĐ thì bỏ qua
            
            return JsonResponse({'success': False, 'message': 'Bỏ qua giao dịch (Không đúng cú pháp hoặc không đủ tiền)'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'message': 'Chỉ nhận phương thức POST'})

# HÀM 2: Cho phép giao diện kiểm tra trạng thái hóa đơn
def check_invoice_status(request, invoice_id):
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        return JsonResponse({'status': invoice.status})
    except Invoice.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)
    

#Hàm tính doanh thu
def report(request):
    base_qs = Invoice.objects.filter(room__owner=request.user)

    available_years = sorted(list(set(d.year for d in base_qs.values_list('billing_month', flat=True) if d)), reverse=True)
    if not available_years:
        available_years = [timezone.now().year]

    selected_year = int(request.GET.get('year', timezone.now().year))
    selected_month = request.GET.get('month', 'all') 

    
    filtered_qs = base_qs.filter(billing_month__year=selected_year)
    
    chart_title = f"Biểu đồ doanh thu năm {selected_year}"
    if selected_month != 'all':
        filtered_qs = filtered_qs.filter(billing_month__month=int(selected_month))
        chart_title = f"Biểu đồ doanh thu Tháng {selected_month}/{selected_year}"

    paid_qs = filtered_qs.filter(status='paid')
    
    total_revenue = paid_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    room_revenue = paid_qs.aggregate(total=Sum('base_rent'))['total'] or 0
    extra_revenue = paid_qs.aggregate(total=Sum('extra_fee'))['total'] or 0
    
    elec_calc = (F('new_electricity') - F('old_electricity')) * F('electricity_price')
    water_calc = (F('new_water') - F('old_water')) * F('water_price')
    utility_revenue = paid_qs.annotate(
        util_total=ExpressionWrapper(elec_calc + water_calc, output_field=IntegerField())
    ).aggregate(total=Sum('util_total'))['total'] or 0

    pending_revenue = filtered_qs.filter(status='unpaid').aggregate(total=Sum('total_amount'))['total'] or 0

    total_breakdown = room_revenue + utility_revenue + extra_revenue
    room_pct = (room_revenue / total_breakdown * 100) if total_breakdown else 0
    util_pct = (utility_revenue / total_breakdown * 100) if total_breakdown else 0
    extra_pct = (extra_revenue / total_breakdown * 100) if total_breakdown else 0
    
    total_expected = total_revenue + pending_revenue
    collection_rate = round((total_revenue / total_expected * 100), 1) if total_expected else 0
    context = {
        'available_years': available_years,
        'selected_year': selected_year,
        'selected_month': selected_month,
        
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'collection_rate': collection_rate,
        
        'room_revenue': room_revenue,
        'room_pct': room_pct,
        'utility_revenue': utility_revenue,
        'util_pct': util_pct,
        'extra_revenue': extra_revenue,
        'extra_pct': extra_pct,
    }
    return render(request, 'app/report.html', context)



