from django.urls import path, include
from .import views
from .statistical import *
from rest_framework import routers

router = routers.DefaultRouter()
router.register('users', views.UserViewSet)
router.register('post', views.PostViewSet)
router.register('coupon', views.CouponViewSet)
router.register('auction', views.AuctionViewSet)
router.register("rate", views.RateViewSet)
router.register("notification",views.NotificationsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('statistical/', statistical, name='statistical'),
]