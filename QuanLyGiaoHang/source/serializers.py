from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from .models import *


class AvatarSerializers(serializers.ModelSerializer):
    avatar = SerializerMethodField(source='avatar')

    def get_avatar(self, user):
        if user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(user.avatar)
            return user.avatar.url
        return None


class CustomerSerializers(serializers.ModelSerializer):
    class Meta:
        model = InfoShipper
        fields = ['identity_number', 'is_authorize']


class UserSerializers(AvatarSerializers):

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'password', 'email', 'avatar', 'role_user']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        data = validated_data.copy()
        user = User(**data)
        user.set_password(data['password'])
        user.save()
        return user


class ShipperSerializers(AvatarSerializers):

    class Meta:
        model = InfoShipper
        fields = ['id', 'first_name', 'last_name', 'username', 'password', 'email', 'avatar', 'role_user', 'identity_number','is_authorize']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        data = validated_data.copy()
        user = InfoShipper(**data)
        user.set_password(data['password'])
        user.save()
        return user


class UserSummarySerializer(AvatarSerializers):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']


class ImagePostSerializer(serializers.ModelSerializer):
    image = SerializerMethodField(source='avatar')

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image)
            return obj.image.url
        return None

    class Meta:
        model = ImagePost
        fields = '__all__'


class AuctionSerializer(serializers.ModelSerializer):
    shipper = UserSummarySerializer()

    class Meta:
        model = Auction
        fields = ['id', 'comment', 'Price_auction', 'shipper']


class PostSerializer(serializers.ModelSerializer):
    customer = UserSummarySerializer()

    class Meta:
        model = Post
        fields = '__all__'


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'


class PostSerializerForCustomer(serializers.ModelSerializer):
    customer = UserSummarySerializer()
    auction = SerializerMethodField()
    shipper = UserSummarySerializer()
    class Meta:
        model = Post
        fields = ['id', 'created_date', "customer", 'payment', 'customer', 'fromLatitude','fromLongitude', 'price', 'category', 'option', 'auction', 'distance', 'name','address','weight','apartmentNumber','status','shipper','nameReceiver',"isRate"]

    def get_auction(self, obj):
        auction = Auction.objects.filter(post_id=obj.id)
        serializer = AuctionSerializer(auction, many=True)
        return serializer.data


class MyAuctionSerializer(serializers.ModelSerializer):
    post = PostSerializer()

    class Meta:
        model = Auction
        fields = ['id', 'Price_auction', 'comment', 'post']


class MyNotificationSerializers(serializers.ModelSerializer):
    Sender = UserSummarySerializer()

    class Meta:
        model = Notification
        fields = '__all__'


class RateSerializers(serializers.ModelSerializer):
    customer = UserSummarySerializer()

    class Meta:
        model = Rate
        fields = '__all__'
