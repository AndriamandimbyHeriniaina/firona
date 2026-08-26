from rest_framework import generics

from apps.catalog.models import Product
from apps.catalog.serializers import ProductSerializer


class ProductListView(generics.ListAPIView):
    """List active products watched by the radar.

    Example:
        GET /api/v1/products/
    """

    serializer_class = ProductSerializer
    queryset = Product.objects.filter(is_active=True).select_related("category")
