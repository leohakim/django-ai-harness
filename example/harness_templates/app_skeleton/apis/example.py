"""Thin API: validate input, call a service or selector, serialize output.

One operation per class. Input and output serializers are nested so they stay local to
the operation instead of becoming a shared, over-general schema.
"""

from rest_framework import serializers
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class ExampleCreateApi(APIView):
    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=255)

    class OutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        name = serializers.CharField()

    def post(self, request: Request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # services.example_create(**serializer.validated_data)
        return Response(
            {"detail": "not implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
