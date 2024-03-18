from .serializers import *


def create_notification(sender, receiver, content):
    temp_notification = Notification.objects.create(
        Receiver=receiver,
        content=content,
        Sender=sender
    )
