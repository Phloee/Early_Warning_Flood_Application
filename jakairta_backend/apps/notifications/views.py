from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import Notification
from .serializers import NotificationSerializer, FCMTokenSerializer


@extend_schema(tags=['Notifications'])
class NotificationListView(generics.ListAPIView):
    """Riwayat notifikasi pengguna"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@extend_schema(tags=['Notifications'])
class MarkReadView(generics.UpdateAPIView):
    """Tandai notifikasi sebagai sudah dibaca"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response(NotificationSerializer(notif).data)


@extend_schema(tags=['Notifications'])
class MarkAllReadView(APIView):
    """Tandai semua notifikasi sebagai sudah dibaca"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': f'{count} notifikasi ditandai sudah dibaca'})


@extend_schema(tags=['Notifications'])
class RegisterFCMTokenView(APIView):
    """Daftarkan FCM device token pengguna"""
    permission_classes = [IsAuthenticated]
    serializer_class = FCMTokenSerializer

    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.fcm_token = serializer.validated_data['fcm_token']
        request.user.save(update_fields=['fcm_token'])
        return Response({'message': 'FCM token berhasil didaftarkan'})
