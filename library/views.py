import requests as http_requests

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Note
from .serializers import BookSerializer, NoteSerializer


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


class NoteViewSet(viewsets.ModelViewSet):
    """
    CRUD for notes nested under a specific book.

    The parent book is resolved from the URL's `book_pk` and must belong
    to the authenticated user.  If it doesn't (or doesn't exist), every
    operation returns 404 — never 403.
    """

    serializer_class = NoteSerializer

    def _get_parent_book(self):
        """Return the parent book scoped to request.user, or raise 404."""
        return get_object_or_404(
            Book,
            pk=self.kwargs['book_pk'],
            user=self.request.user,
        )

    def get_queryset(self):
        book = self._get_parent_book()
        return Note.objects.filter(book=book)

    def perform_create(self, serializer):
        book = self._get_parent_book()
        serializer.save(book=book)


class CoverSearchView(APIView):
    """
    Search Open Library for book covers.

    GET /api/books/cover-search/?q=<query>

    Returns a list of candidates with title, author, and cover_url.
    Results without a cover image are excluded. Failures and timeouts
    return an empty list (200), not a 500.
    """

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'results': []})

        try:
            resp = http_requests.get(
                'https://openlibrary.org/search.json',
                params={'q': query, 'limit': 5},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
        except (http_requests.RequestException, ValueError):
            return Response({'results': []})

        results = []
        for doc in data.get('docs', []):
            cover_i = doc.get('cover_i')
            if not cover_i:
                continue

            results.append({
                'title': doc.get('title', ''),
                'author': ', '.join(doc.get('author_name', [])),
                'cover_url': f'https://covers.openlibrary.org/b/id/{cover_i}-M.jpg',
            })

        return Response({'results': results})


