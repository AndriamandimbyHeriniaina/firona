from django.http import Http404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Product
from apps.catalog.serializers import ProductSerializer
from apps.catalog.services import build_product_detail


class ProductListView(generics.ListAPIView):
    """List active products watched by the radar.

    Example:
        GET /api/v1/products/
    """

    serializer_class = ProductSerializer
    queryset = Product.objects.filter(is_active=True).select_related("category")


class ProductDetailView(APIView):
    """Full article card: copy, images, where to buy, sources, radar.

    Example:
        GET /api/v1/products/telephone/
    """

    def get(self, _request, slug: str):
        try:
            payload = build_product_detail(slug)
        except Product.DoesNotExist as exc:
            raise Http404("Unknown article") from exc
        return Response(payload)
