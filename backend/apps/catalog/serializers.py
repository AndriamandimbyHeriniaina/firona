from rest_framework import serializers

from apps.catalog.models import Category, Product
from apps.sources.models import Source


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class SourceBriefSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    collectable = serializers.BooleanField(source="can_collect", read_only=True)
    block_reason = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Source
        fields = (
            "id",
            "name",
            "kind",
            "kind_label",
            "consent_granted",
            "collectable",
            "block_reason",
        )


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "aliases",
            "description",
            "image_url",
            "gallery",
            "where_to_find",
        )


class ProductDetailSerializer(ProductSerializer):
    sources = SourceBriefSerializer(many=True, read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ("sources",)
