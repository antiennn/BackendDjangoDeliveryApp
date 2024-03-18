from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import *
import cloudinary.uploader
from . import perms
import requests
import vnpay
from .notifications import create_notification
from .utils import sendEmail


class VNPayCheckoutAPI(APIView):
    def post(self, request, *args, **kwargs):
        # Get necessary data from request
        amount = request.data.get('amount')
        order_info = request.data.get('order_info')

        # Generate VNPay payment data
        payment_data = vnpay.create_payment_data(amount=amount, order_info=order_info)

        # In a real-world application, you might want to save payment_data in your database
        # and return a unique identifier or token for this transaction

        return Response(payment_data)


class UserViewSet(viewsets.ViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action.__eq__('create_post'):
            return [perms.CustomerAuthenticated()]

    @action(methods=['POST'], detail=False, url_path='register')
    def register(self, request):
        try:
            data = request.data
            role = data.get("role")
            if data.get("image"):
                res = cloudinary.uploader.upload(data.get("image"), folder="avatar/")
            else:
                return Response({"detail": f"Please choice your avatar"}, status=status.HTTP_400_BAD_REQUEST)
            if role.__eq__("Shipper"):
                temp_user = InfoShipper.objects.create_user(
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    username=data.get('username'),
                    email=data.get('email'),
                    password=data.get('password'),
                    role_user=role,
                    avatar=res['url'],
                    identity_number=data.get('identity_number'),
                )
                serializer = ShipperSerializers(temp_user, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                temp_user = User.objects.create_user(
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    username=data.get('username'),
                    email=data.get('email'),
                    password=data.get('password'),
                    role_user=role,
                    avatar=res['secure_url'],
                )
                serializer = UserSerializers(temp_user, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"detail": f"Error updating user: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def get_permissions(self):
        if self.action.__eq__('current_user'):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['GET'], detail=False, url_path='current_user', url_name='current_user')
    def current_user(self, request):
        return Response(UserSerializers(request.user).data, status=status.HTTP_200_OK)


class PostViewSet(viewsets.ViewSet, generics.ListAPIView, generics.DestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [perms.OwnerAuthenticated]

    def get_queryset(self):
        queries = self.queryset.filter(status="auctioning")
        filtered = []
        latitude = self.request.query_params.get("latitude")
        longitude = self.request.query_params.get("longitude")
        if latitude and longitude:
            for query in queries:
                response = requests.get(
                    f"https://dev.virtualearth.net/REST/v1/Routes/Driving?o=json&wp.0={latitude},{longitude}&wp.1={query.fromLatitude},{query.fromLongitude}&key=AiG0p7k1VuqiubVqZ22aZXS6HEih9Yg95wRzucCj_gRvT0HeaMMuanyX13L4qGfd")
                data = response.json()
                if data.get("resourceSets")[0].get("resources")[0].get("travelDistance") < 1:
                    filtered.append(query)
            return filtered
        return queries

    def get_permissions(self):
        if self.action == 'auction':
            return [perms.ShipperAuthenticated()]
        if self.action in ['create_post', 'newestPost']:
            return [perms.CustomerAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['POST'], detail=False, url_name='create_post')
    def create_post(self, request):
        try:
            data = request.data
            temp_post = Post.objects.create(
                name=data.get('namepost'),
                customer=request.user,
                fromLatitude=data.get('startlatitude'),
                fromLongitude=data.get('startlongitude'),
                toLatitude=data.get('endlatitude'),
                toLongitude=data.get('endlongitude'),
                payment=data.get('payment'),
                distance=data.get('distance'),
                price=data.get('price'),
                phoneReceiver=data.get('phonereceiver'),
                category=data.get('category'),
                option=data.get('option'),
                apartmentNumber=data.get('address'),
                address=data.get('query'),
                weight=data.get('weight'),
                nameReceiver=data.get('namereceiver')
            )
            return Response(PostSerializerForCustomer(temp_post).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": f"Error create post: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='auction', detail=True, url_name="auction")
    def add_auction(self, request, pk):
        try:
            auction = Auction.objects.filter(post=self.get_object())
            for a in auction:
                if a.shipper == request.user:
                    return Response({"detail": "You bid on this shipment"}, status=status.HTTP_400_BAD_REQUEST)
            a = Auction.objects.create(shipper=request.user, post=self.get_object(),
                                       comment=request.data.get('comment'),
                                       Price_auction=request.data.get('price_auction'))
            create_notification(request.user, self.get_object().customer, "Have bit your post")
            return Response(AuctionSerializer(a).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"detail": f"Error create post: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], url_path='newest', detail=False, url_name="newestPost")
    def newest_post(self, request):
        myPost = Post.objects.all().filter(customer_id=request.user.id).last()
        return Response(PostSerializerForCustomer(myPost).data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path="accept_auction", detail=True, url_name="accept_auction")
    def accept_auction(self, request, pk):
        try:
            myPost = self.get_object()
            temp_auction = Auction.objects.all().filter(id=request.data.get("id"))
            myPost.shipper_id = temp_auction[0].shipper_id
            myPost.price = temp_auction[0].Price_auction
            myPost.status = "In transit"
            myPost.save()
            ###
            create_notification(request.user, myPost.shipper, f"have bit successfully the post {myPost.id}")
            sendEmail(f"Your bit was successful in the post have id is {myPost.id}",
                      [User.objects.get(pk=temp_auction[0].shipper_id).email])
            ###
            auctionInPost = Auction.objects.all().filter(post_id=myPost.id)
            auctionFail = [obj for obj in auctionInPost if obj.shipper_id != myPost.shipper_id]
            emailFail = [User.objects.get(pk=auction.shipper_id).email for auction in auctionFail]
            sendEmail(f"Unfortunately, your bid was unsuccessful in post have id is {myPost.id}", emailFail)
            return Response(PostSerializerForCustomer(myPost).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Error create post: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], url_path='my_post', detail=False, url_name="my_post")
    def my_post(self, request):
        temp_post = self.queryset.filter(customer=request.user).exclude(status="complete")
        return Response(PostSerializerForCustomer(temp_post, many=True).data, status=status.HTTP_200_OK)

    @action(methods=['get'], url_path='my_post_complete', detail=False, url_name="my_post_complete")
    def my_post_complete(self, request):
        temp_post = self.queryset.filter(customer=request.user, status="complete")
        return Response(PostSerializerForCustomer(temp_post, many=True).data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='complete_delivery', detail=False, url_name="complete_delivery")
    def complete_delivery(self, request):
        temp_post = self.queryset.get(pk=request.data.get("id"))
        temp_post.status = "complete"
        temp_post.save()
        return Response(PostSerializerForCustomer(temp_post).data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path="post_rate", detail=False, url_name="post_rate")
    def post_rate(self, request):
        try:
            data = request.data
            myPost = self.queryset.get(pk=data.get("id"))
            if myPost.isRate:
                return Response({"detail": "You have rate this post"}, status=status.HTTP_400_BAD_REQUEST)
            temp_rate = Rate.objects.create(
                customer=request.user,
                comment=data.get("comment"),
                rate=data.get("rate"),
                shipper=myPost.shipper
            )
            myPost.isRate = True
            myPost.save()
            return Response(RateSerializers(temp_rate).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"detail": f"Error create post: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class AuctionViewSet(viewsets.ViewSet, generics.DestroyAPIView):
    queryset = Auction.objects.all()
    permission_classes = [perms.OwnerAuthenticated]
    serializer_class = MyAuctionSerializer

    @action(methods=['get'], detail=False, url_name="my_auction")
    def my_auction(self, request):
        my_auction = self.queryset.filter(shipper=request.user.id)
        my_auction_not_complete = [obj for obj in my_auction if Post.objects.get(pk=obj.post_id).status != "complete"]
        return Response(MyAuctionSerializer(my_auction_not_complete, many=True).data, status=status.HTTP_200_OK)

    @action(methods=['patch'], detail=True, url_name="update_auction")
    def update_auction(self, request, pk):
        try:
            data = request.data
            temp_auction = self.get_object()

            for key, value in data.items():
                setattr(temp_auction, key, value)

            temp_auction.save()
            return Response(MyAuctionSerializer(temp_auction).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Error create post: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class CouponViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer


class RateViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Rate.objects.all()
    serializer_class = RateSerializers

    def list(self, request, *args, **kwargs):
        id = request.query_params.get('id')
        temp_rate = self.queryset.filter(shipper_id=id)
        return Response(RateSerializers(temp_rate, many=True).data, status=status.HTTP_200_OK)


class NotificationsViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = MyAuctionSerializer

    def list(self, request, *args, **kwargs):
        temp_notification = self.queryset.filter(Receiver=request.user)
        return Response(MyNotificationSerializers(temp_notification, many=True).data, status=status.HTTP_200_OK)
