from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import calendar
from datetime import date
# Create your models here.

#Tạo bảng profile để gắn thẻ cho chủ trọ
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_renters', null=True, blank=True)
    
    def __str__(self):
        return self.user.username


#Phòng
class Room(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_rooms', null=True, blank=True)
    #1. Thông tin cơ bản
    name = models.IntegerField(verbose_name="Tên phòng", error_messages={"invalid": "Tên phòng chỉ được là số (Lưu ý: Số đầu tiên là số tầng)"})
    floor = models.IntegerField(verbose_name="Tầng", error_messages={"invalid": "Số tầng chỉ được là số"})
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
        ('Đã cọc', 'Đã cọc'),
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
        if self.status not in ['Đang thuê', 'Đã cọc']:
            return "Trống"

        latest_contract = self.contracts.order_by('-start_date').first()
        if latest_contract and latest_contract.renter:
            return f"{latest_contract.renter.last_name} {latest_contract.renter.first_name}"
        return "Trống"

    @property
    def active_contract(self):
        # CHỐT CHẶN 2: Giải quyết cột Ngày thuê và Ngày hết hạn
        # Nếu trạng thái không phải 'Đang thuê', lập tức trả về None (Để HTML in ra dấu -)
        if self.status not in ['Đang thuê', 'Đã cọc']:
            return None

        return self.contracts.order_by('-start_date').first()
    class Meta:
        unique_together = ('owner', 'name')

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
            month = self.start_date.month - 1 + self.duration
            year = self.start_date.year + month // 12
            month = month % 12 + 1
            day = min(self.start_date.day, calendar.monthrange(year, month)[1])
            return date(year, month, day)
        return None

    #Bảng tài liệu ảnh hợp đồng
class ContractDocument(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='contracts/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


#Bảng hóa đơn
class Invoice(models.Model):
    # Các trạng thái của hóa đơn
    STATUS_CHOICES = (
        ('draft', 'Lưu nháp'),
        ('unpaid', 'Chưa thanh toán'),
        ('paid', 'Đã thanh toán'),
    )

    # Liên kết với bảng Room. Nếu xóa phòng, hóa đơn của phòng đó cũng bị xóa (CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='invoices', verbose_name="Phòng")

    #Liên kết với bảng User. Nếu lỡ xóa user thì hóa đơn vẫn còn đó và để trống tên
    renter = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='invoices', 
        verbose_name="Người thuê"
    )
    
    # Kỳ hóa đơn (lưu ngày 1 của tháng đó để dễ sort/lọc dữ liệu)
    billing_month = models.DateField(verbose_name="Kỳ hóa đơn") 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid', verbose_name="Trạng thái")

    # 2. SNAPSHOT ĐƠN GIÁ (Bắt buộc phải lưu cứng lại để không bị ảnh hưởng nếu sau này đổi giá phòng)
    base_rent = models.IntegerField(default=0, verbose_name="Tiền thuê phòng")
    electricity_price = models.IntegerField(default=0, verbose_name="Đơn giá điện")
    water_price = models.IntegerField(default=0, verbose_name="Đơn giá nước")
    trash_price = models.IntegerField(default=0, verbose_name="Tiền rác")
    internet_price = models.IntegerField(default=0, verbose_name="Tiền internet")

    # 3. CHỈ SỐ ĐIỆN NƯỚC
    old_electricity = models.IntegerField(default=0, verbose_name="Chỉ số điện cũ")
    new_electricity = models.IntegerField(default=0, verbose_name="Chỉ số điện mới")
    old_water = models.IntegerField(default=0, verbose_name="Chỉ số nước cũ")
    new_water = models.IntegerField(default=0, verbose_name="Chỉ số nước mới")

    # 4. PHỤ PHÍ & TỔNG TIỀN
    extra_fee = models.IntegerField(default=0, verbose_name="Phụ phí khác")
    extra_fee_reason = models.TextField(blank=True, null=True, verbose_name="Lý do phụ phí")
    total_amount = models.IntegerField(default=0, verbose_name="Tổng cộng thanh toán")

    # 5. THỜI GIAN TẠO
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hóa đơn"
        ordering = ['-billing_month', '-created_at']

        #Điều kiện ràng buộc 1 căn hộ không được có 2 hóa đơn cùng tháng
        constraints = [
            models.UniqueConstraint(
                fields=['room', 'billing_month'], 
                name='unique_invoice_per_room_per_month'
            )
        ]
    def get_elec_cost(self):
        return (self.new_electricity - self.old_electricity) * self.electricity_price
    def get_water_cost(self):
        return (self.new_water - self.old_water) * self.water_price
    def __str__(self):
        renter_name = f" - {self.renter.get_full_name()}" if self.renter else "Khách đã trả phòng"
        return f"Hóa đơn {self.room.name}{renter_name} - Kỳ {self.billing_month.strftime('%m/%Y')}"