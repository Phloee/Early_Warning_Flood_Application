from django.urls import path
from .views import AreaListView, AreaDetailView, SavedAreaListCreateView, SavedAreaDeleteView

urlpatterns = [
    path('', AreaListView.as_view(), name='area-list'),
    path('<int:pk>/', AreaDetailView.as_view(), name='area-detail'),
    path('saved/', SavedAreaListCreateView.as_view(), name='saved-area-list'),
    path('saved/<int:pk>/', SavedAreaDeleteView.as_view(), name='saved-area-delete'),
]
