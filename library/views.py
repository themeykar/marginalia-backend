from rest_framework import viewsets

from .models import Book
from .serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    """
    CRUD for the authenticated user's books.

    Queryset is scoped to request.user so that books belonging to other
    users are invisible — requests for another user's book return 404,
    never 403.
    """

    serializer_class = BookSerializer

    def get_queryset(self):
        qs = Book.objects.filter(user=self.request.user)

        # Optional status filter: /api/books/?status=reading
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
