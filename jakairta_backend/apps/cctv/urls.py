from django.urls import path
from .views import CCTVListView, CCTVDetailView

urlpatterns = [
    path('', CCTVListView.as_view(), name='cctv-list'),
    path('<int:pk>/', CCTVDetailView.as_view(), name='cctv-detail'),
]
