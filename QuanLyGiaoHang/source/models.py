from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
import uuid


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "Admin", "Admin"
        CUSTOMER = "Customer", "Customer"
        SHIPPER = "Shipper", "Shipper"
    avatar = CloudinaryField('avatar', null=True)
    role_user = models.CharField(max_length=10, choices=Role.choices)


class InfoShipper(User):
    identity_number = models.CharField(max_length=12, null=True)
    is_authorize = models.BooleanField(default=False)
    user_ptr = models.OneToOneField(User, on_delete=models.CASCADE, parent_link=True,primary_key=True)


class Post(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20)
    customer = models.ForeignKey(User, models.CASCADE)
    fromLatitude = models.FloatField(null=True)
    fromLongitude = models.FloatField(null=True)
    toLatitude = models.FloatField(null=True)
    toLongitude = models.FloatField(null=True)
    payment = models.TextField(max_length=50, null=True)
    distance = models.FloatField(null=True)
    price = models.FloatField(null=True)
    phoneReceiver = models.CharField(max_length=12, null=True)
    category = models.TextField(max_length=10, null=True)
    option = models.TextField(null=True)
    apartmentNumber = models.CharField(max_length=10,null=True)
    address = models.TextField(max_length=50, null=True)
    weight = models.TextField(max_length=50, null=True)
    status = models.TextField(default="auctioning")
    shipper = models.ForeignKey(User,models.CASCADE,null=True,related_name='shipper')
    nameReceiver = models.TextField(null=True)
    isRate = models.BooleanField(default=False)


class ImagePost(BaseModel):
    post = models.ForeignKey(Post, models.CASCADE)
    image = CloudinaryField('image')


class Auction(BaseModel):
    shipper = models.ForeignKey(User, models.CASCADE)
    post = models.ForeignKey(Post, models.CASCADE)
    Price_auction = models.FloatField(validators=[MinValueValidator(0.0)])
    comment = models.CharField(max_length=255, null=True)


class Coupon(BaseModel):
    name = models.TextField(null=True)
    start_date = models.DateField(null=True)
    expiration_date = models.DateField(null=False)
    percent_discount = models.FloatField(null=False)
    Minimum_price = models.FloatField(null=False)


class Notification(BaseModel):
    Receiver = models.ForeignKey(User, models.CASCADE)
    Sender = models.ForeignKey(User,models.CASCADE, null=True, related_name="sender")
    content = models.TextField(null=True)
    is_read = models.BooleanField(default=False)


class Rate(BaseModel):
    customer = models.ForeignKey(User, models.SET_DEFAULT, default="Người dùng app")
    shipper = models.ForeignKey(User, models.CASCADE, null=True, related_name='shipperrate')
    rate = models.SmallIntegerField(default=0)
    comment = models.TextField(max_length=200, null=True)
