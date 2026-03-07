from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import calendar
from datetime import date
# Create your models here.
#Phòng
class Room(models.Model):
    #1. Thông tin cơ bản
    name = models.CharField(max_length=50, verbose_name="Tên phòng")
    floor = models.IntegerField(verbose_name="Tầng")
    area = models.FloatField(verbose_name="Diện tích (m2)")
    max_occupancy = models.IntegerField(default=1, verbose_name="Số người tối đa")

    # Dùng IntegerField cho tiền VNĐ vì không có số thập phân
    base_rent = models.IntegerField(verbose_name="Giá thuê cơ bản")

    # --- 2. TIỆN NGHI PHÒNG (Boolean) ---
    air_conditioner = models.BooleanField(default=False, verbose_name="Máy lạnh")
    water_heater = models.BooleanField(default=False, verbose_name="Máy nước nóng")
    refrigerator = models.BooleanField(default=False, verbose_name="Tủ lạnh")
    furniture = models.BooleanField(default=False, verbose_name="Giường/Tủ")
    balcony = models.BooleanField(default=False, verbose_name="Ban công")

    #Đơn giá các dịch vụ
    electricity_price = models.IntegerField(verbose_name="Đơn giá Điện")
    water_price = models.IntegerField(verbose_name="Đơn giá Nước")
    trash_price = models.IntegerField( verbose_name="Rác")
    internet_price = models.IntegerField( verbose_name="Internet")

    #Chỉ số điện và nước hiện tại
    current_electricity = models.IntegerField(default=0, verbose_name="Chỉ số điện hiện tại")
    current_water= models.IntegerField(default=0, verbose_name="Chỉ số nước hiện tại")

    # --- 5. TRẠNG THÁI PHÒNG ---
    STATUS_CHOICES = (
        ('Trống', 'Trống'),
        ('Đang thuê', 'Đang thuê'),
        ('Sửa chữa', 'Sửa chữa'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Trống', verbose_name="Trạng thái")

    # Tracking thời gian tạo/cập nhật
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.floor}"

    @property
    def current_renter(self):
        # CHỐT CHẶN 1: Giải quyết cột Người thuê
        # Nếu trạng thái không phải 'Đang thuê', lập tức trả về chữ 'Trống'
        if self.status != 'Đang thuê':
            return "Trống"

        latest_contract = self.contracts.order_by('-start_date').first()
        if latest_contract and latest_contract.renter:
            return f"{latest_contract.renter.last_name} {latest_contract.renter.first_name}"
        return "Trống"

    @property
    def active_contract(self):
        # CHỐT CHẶN 2: Giải quyết cột Ngày thuê và Ngày hết hạn
        # Nếu trạng thái không phải 'Đang thuê', lập tức trả về None (Để HTML in ra dấu -)
        if self.status != 'Đang thuê':
            return None

        return self.contracts.order_by('-start_date').first()

#Thông tin cơ bản người thuê
class Contract(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='contracts', verbose_name="Phòng")

    # on_delete=models.SET_NULL: Nếu lỡ xóa User, Hợp đồng vẫn còn lưu lại tên
    renter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenant_contracts',
                               verbose_name="Người thuê")
    phone_validator = RegexValidator(
        regex=r'^\d{10}$',
        message="Số điện thoại không hợp lệ. Bắt buộc nhập đúng 10 chữ số."
    )
    phone_number = models.CharField(
        max_length=10,
        validators=[phone_validator],
        verbose_name="Số điện thoại"
    )

    identify_validator = RegexValidator(
        regex=r'^\d{12}$',
        message="CCCD không hợp lệ. Bắt buộc nhập đúng 12 chữ số."
    )

    identify = models.CharField(
        max_length=12,
        validators=[identify_validator],
        verbose_name="CCCD"
    )
    #Thông tin hợp đồng
    start_date = models.DateField(verbose_name="Ngày dọn vào")

    # Thời hạn: 3 tháng, 6 tháng, 12 tháng... (Lưu số nguyên, ví dụ vô thời hạn thì lưu số 0)
    duration = models.IntegerField(default=3, verbose_name="Thời hạn HĐ (Tháng)")

    deposit = models.IntegerField(verbose_name="Tiền cọc giữ chỗ")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        renter_name = self.renter.get_full_name()
        return f"HĐ {self.room.name} - Khách: {renter_name}"

    @property
    def end_date(self):
        if self.duration == 0:
            return "Vô thời hạn"

        if self.start_date:
            # Thuật toán cộng tháng an toàn trong Python
            month = self.start_date.month - 1 + self.duration
            year = self.start_date.year + month // 12
            month = month % 12 + 1
            # Đảm bảo không bị lỗi nếu cộng tháng rơi vào ngày 31 mà tháng đó chỉ có 30 ngày
            day = min(self.start_date.day, calendar.monthrange(year, month)[1])
            return date(year, month, day)
        return None

    #Bảng tài liệu ảnh hợp đồng
class ContractDocument(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='contracts/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
