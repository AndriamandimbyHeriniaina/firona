from rest_framework import serializers


class RadarItemSerializer(serializers.Serializer):
    product = serializers.DictField()
    horizon = serializers.CharField()
    score = serializers.IntegerField()
    demand_score = serializers.IntegerField()
    supply_score = serializers.IntegerField()
    momentum = serializers.FloatField()
    emerging_score = serializers.IntegerField()
    label = serializers.CharField()
    captured_at = serializers.DateTimeField()
