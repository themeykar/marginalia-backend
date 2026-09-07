from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .serializers import SignupSerializer, UserSerializer


class SignupView(generics.CreateAPIView):
    """Register a new user. Public endpoint — no token required."""

    serializer_class = SignupSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveAPIView):
    """Return the currently authenticated user's profile."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
