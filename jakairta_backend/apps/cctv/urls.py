from django.urls import path
from .views import CCTVListView, CCTVDetailView, Yolov8WebhookView, VideoSimulasiListView

urlpatterns = [
    path('', CCTVListView.as_view(), name='cctv-list'),
    path('<int:pk>/', CCTVDetailView.as_view(), name='cctv-detail'),
    path('simulations/', VideoSimulasiListView.as_view(), name='cctv-simulations'),
    path('webhook/', Yolov8WebhookView.as_view(), name='cctv-webhook'),
]
