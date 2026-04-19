from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Area, SavedArea
from .serializers import AreaSerializer, AreaListSerializer, SavedAreaSerializer


@extend_schema(tags=['Areas'])
class AreaListView(generics.ListAPIView):
    """Daftar semua wilayah yang dipantau beserta status banjir"""
    serializer_class = AreaListSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'district', 'sub_district']
    ordering_fields = ['name', 'district', 'status', 'water_level_cm', 'updated_at']
    ordering = ['district', 'name']

    def get_queryset(self):
        qs = Area.objects.filter(is_active=True)
        status_filter = self.request.query_params.get('status')
        district_filter = self.request.query_params.get('district')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if district_filter:
            qs = qs.filter(district__icontains=district_filter)
        return qs


@extend_schema(tags=['Areas'])
class AreaDetailView(generics.RetrieveAPIView):
    """Detail wilayah spesifik"""
    serializer_class = AreaSerializer
    permission_classes = [AllowAny]
    queryset = Area.objects.filter(is_active=True)


@extend_schema(tags=['Saved Areas'])
class SavedAreaListCreateView(generics.ListCreateAPIView):
    """Daftar wilayah tersimpan pengguna / simpan wilayah baru"""
    serializer_class = SavedAreaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedArea.objects.filter(user=self.request.user).select_related('area')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Cegah duplikat
        area = serializer.validated_data['area']
        if SavedArea.objects.filter(user=request.user, area=area).exists():
            return Response({'error': 'Wilayah sudah disimpan'}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Saved Areas'])
class SavedAreaDeleteView(generics.DestroyAPIView):
    """Hapus wilayah tersimpan"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedArea.objects.filter(user=self.request.user)
