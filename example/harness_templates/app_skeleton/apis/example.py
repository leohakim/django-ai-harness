"""Thin API example — validate, call service/selector, serialize."""

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class ExampleCreateApi(APIView):
    def post(self, request: Request) -> Response:
        # validate with InputSerializer, call services.example_create, return OutputSerializer
        return Response({"detail": "not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)
