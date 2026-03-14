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
from .models import Room, Contract, ContractDocument, Invoice
from datetime import datetime, date

# Create your views here.
def home_admin(request):
    rooms = Room.objects.all().order_by('floor')
    context = {'rooms': rooms}
    return render(request, 'app/home_admin.html', context)
def add_room(request):
    if request.method == 'POST':
        try:
            # 1. HÀM DỌN DẸP SỐ (Quét sạch dấu chấm, dấu phẩy để tránh lỗi '1,250')
            def to_int(value):
                if not value: return 0
                return int(str(value).replace('.', '').replace(',', '').strip())

            # 2. LẤY VÀ ĐỒNG BỘ THÔNG TIN PHÒNG
            name = request.POST.get('name', '').strip()
            if Room.objects.filter(name=name).exists():
                messages.error(request, f"Lỗi: Phòng {name} đã tồn tại!")
                return redirect('add_room')
            floor = request.POST.get('floor', '1')
            area = float(request.POST.get('area') or 0)
            max_occupancy = to_int(request.POST.get('max_occupancy'))

            # ĐỒNG BỘ TRẠNG THÁI: Chuyển Anh (available) sang Việt (Trống)
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
            # In lỗi ra màn hình đen để bạn biết chính xác dòng nào sai
            print(f"LỖI THÊM PHÒNG: {e}")
            messages.error(request, f"Lỗi hệ thống: {e}")
            return redirect('add_room')

    # GET REQUEST
    users = User.objects.filter(is_staff=False)
    context = {'users': users}
    return render(request, 'app/add_room.html', context)

def delete_room(request, room_id):
    room = Room.objects.get(id=room_id)
    room.delete()
    messages.success(request, f"Đã xóa phòng {room.name} thành công!")
    return redirect('home_admin')


def edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    users = User.objects.filter(is_staff=False)

    if request.method == 'POST':
        try:
            # 1. HÀM DỌN DẸP SỐ (Quét sạch dấu chấm, dấu phẩy để tránh lỗi '1,250')
            def to_int(value):
                if not value: return 0
                return int(str(value).replace('.', '').replace(',', '').strip())

            # 2. CẬP NHẬT THÔNG TIN PHÒNG
            new_name = request.POST.get('name', '').strip()
            if Room.objects.filter(name=new_name).exclude(id=room_id).exists():
                messages.error(request,
                               f"Lỗi: Không thể đổi số phòng thành '{new_name}' vì đã có phòng khác sử dụng!")
                return redirect('edit_room', room_id=room_id)
            room.name = new_name
            room.floor = request.POST.get('floor', '1')
            room.area = float(request.POST.get('area') or 0)
            room.max_occupancy = to_int(request.POST.get('max_occupancy'))

            # ĐỒNG BỘ TRẠNG THÁI (Chuyển Anh sang Việt để hiện màu ở home_admin)
            status_map = {'available': 'Trống', 'rented': 'Đang thuê', 'maintenance': 'Sửa chữa','deposited': 'Đã cọc' }
            form_status = request.POST.get('status', 'available')
            room.status = status_map.get(form_status, 'Trống')

            # Áp dụng to_int cho TẤT CẢ các trường số
            room.base_rent = to_int(request.POST.get('base_rent'))
            room.electricity_price = to_int(request.POST.get('electricity_price'))
            room.water_price = to_int(request.POST.get('water_price'))
            room.trash_price = to_int(request.POST.get('trash_price'))
            room.internet_price = to_int(request.POST.get('internet_price'))

            room.current_electricity = to_int(request.POST.get('current_electricity'))
            room.current_water = to_int(request.POST.get('current_water'))

            # Tiện nghi
            room.air_conditioner = request.POST.get('air_conditioner') == 'on'
            room.water_heater = request.POST.get('water_heater') == 'on'
            room.refrigerator = request.POST.get('refrigerator') == 'on'
            room.furniture = request.POST.get('furniture') == 'on'
            room.balcony = request.POST.get('balcony') == 'on'

            room.save()  # Lưu bảng Room

            # 3. XỬ LÝ HỢP ĐỒNG (Phải dùng chữ tiếng Việt 'Đang thuê' để khớp logic)
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
                        # Cập nhật thông tin vào hợp đồng hiện có
                        contract.renter = selected_user
                        contract.start_date = start_date
                        contract.duration = duration
                        contract.deposit = deposit
                        contract.identify = identify
                        contract.phone_number = phone_number
                        contract.save()
                    else:
                        # Tạo mới nếu chưa có
                        contract = Contract.objects.create(
                            room=room, renter=selected_user, start_date=start_date,
                            duration=duration, deposit=deposit, identify=identify,
                            phone_number=phone_number
                        )

                    # XỬ LÝ ẢNH: Xóa ảnh cũ & Thêm ảnh mới
                    delete_ids = request.POST.getlist('delete_documents')
                    if delete_ids:
                        ContractDocument.objects.filter(id__in=[did for did in delete_ids if did]).delete()

                    files = request.FILES.getlist('document_file')
                    for f in files:
                        ContractDocument.objects.create(contract=contract, file=f)

            messages.success(request, f"Đã cập nhật thông tin phòng {room.name} thành công!")
            return redirect('home_admin')

        except Exception as e:
            # Hiện lỗi để bạn biết dòng nào hỏng thay vì chỉ refresh âm thầm
            return redirect('edit_room', room_id=room_id)

    return render(request, 'app/add_room.html', {'users': users, 'room': room})
def add_invoice(request, room_id):
   # Lấy thông tin phòng, nếu không có trả về 404
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        billing_date = request.POST.get('billing_month')
        new_elec = int(request.POST.get('new_electricity', 0))
        new_water = int(request.POST.get('new_water', 0))
        extra_fee = int(request.POST.get('extra_fee', '0').replace('.', ''))
        reason = request.POST.get('extra_fee_reason', '')
        action = request.POST.get('action') # 'unpaid' hoặc 'draft'

        # Tính toán tiền bạc
        old_elec = room.current_electricity or 0
        old_water = room.current_water or 0
        
        elec_usage = max(0, new_elec - old_elec)
        water_usage = max(0, new_water - old_water)
        
        total = (room.base_rent + 
                 (elec_usage * room.electricity_price) + 
                 (water_usage * room.water_price) + 
                 room.trash_price + room.internet_price + extra_fee)

        # Lưu vào Database
        Invoice.objects.create(
            room=room, billing_month=billing_date, status=action,
            base_rent=room.base_rent, electricity_price=room.electricity_price,
            water_price=room.water_price, trash_price=room.trash_price,
            internet_price=room.internet_price, old_electricity=old_elec,
            new_electricity=new_elec, old_water=old_water, new_water=new_water,
            extra_fee=extra_fee, extra_fee_reason=reason, total_amount=total
        )

        # Nếu là hóa đơn thật (không phải nháp), cập nhật số mới vào Phòng
        if action == 'unpaid':
            room.current_electricity = new_elec
            room.current_water = new_water
            room.save()

        messages.success(request, "Đã lưu hóa đơn thành công!")
        return redirect('home_admin')

    # Khi vừa nhấn vào icon hóa đơn (GET)
    context = {
        'room': room,
        'today': date.today().strftime('%Y-%m-%d'),
    }
    return render (request, 'app/add_invoice.html', context)