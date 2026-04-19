from django.urls import path
from .views import NotificationListView, MarkReadView, MarkAllReadView, RegisterFCMTokenView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/read/', MarkReadView.as_view(), name='notification-read'),
    path('read-all/', MarkAllReadView.as_view(), name='notification-read-all'),
    path('fcm-token/', RegisterFCMTokenView.as_view(), name='fcm-token-register'),
]
