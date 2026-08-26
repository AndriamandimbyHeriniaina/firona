from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trends.serializers import RadarItemSerializer
from apps.trends.services import VALID_HORIZONS, build_radar


class RadarView(APIView):
    """Market radar for one time horizon.

    Example:
        GET /api/v1/radar/?horizon=now
        GET /api/v1/radar/?horizon=past
        GET /api/v1/radar/?horizon=future
    """

    def get(self, request):
        horizon = request.query_params.get("horizon", "now")
        if horizon not in VALID_HORIZONS:
            horizon = "now"
        payload = build_radar(horizon=horizon)
        return Response(RadarItemSerializer(payload, many=True).data)
