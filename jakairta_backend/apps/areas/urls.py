from django.urls import path
from .views import AreaListCreateView, AreaRetrieveUpdateDestroyView, SavedAreaListCreateView, SavedAreaDeleteView

urlpatterns = [
    path('', AreaListCreateView.as_view(), name='area-list'),
    path('<int:pk>/', AreaRetrieveUpdateDestroyView.as_view(), name='area-detail'),
    path('saved/', SavedAreaListCreateView.as_view(), name='saved-area-list'),
    path('saved/<int:pk>/', SavedAreaDeleteView.as_view(), name='saved-area-delete'),
]
