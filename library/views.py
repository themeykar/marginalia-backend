import requests as http_requests
from collections import Counter
from datetime import date

from django.db.models import Count, Sum
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


class WrapupView(APIView):
    """
    Year in Books aggregation.

    GET /api/wrapup/?year=<year>

    Computes reading stats for the authenticated user's books finished
    in the given year (defaults to current year).
    """

    def get(self, request):
        year = request.query_params.get('year')
        if year:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = date.today().year
        else:
            year = date.today().year

        # All books finished by this user in the requested year
        books = Book.objects.filter(
            user=request.user,
            status='read',
            date_finished__year=year,
        )

        total_books = books.count()

        # -- Empty-state shortcut --
        if total_books == 0:
            return Response({
                'year': year,
                'total_books': 0,
                'total_pages': 0,
                'favorite_genre': None,
                'longest_book': None,
                'most_quoted_book': None,
                'reading_streak': 0,
            })

        # total_pages (treat null page_count as 0)
        total_pages = books.aggregate(
            total=Sum('page_count'),
        )['total'] or 0

        # favorite_genre (mode — null on tie or no genres)
        favorite_genre = self._compute_favorite_genre(books)

        # longest_book
        longest_book = self._compute_longest_book(books)

        # most_quoted_book
        most_quoted_book = self._compute_most_quoted_book(books)

        # reading_streak (consecutive months)
        reading_streak = self._compute_reading_streak(books)

        return Response({
            'year': year,
            'total_books': total_books,
            'total_pages': total_pages,
            'favorite_genre': favorite_genre,
            'longest_book': longest_book,
            'most_quoted_book': most_quoted_book,
            'reading_streak': reading_streak,
        })

    # ----- helpers -----

    @staticmethod
    def _book_card(book, **extra):
        """Serialize a book into the minimal card the frontend needs."""
        card = {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'cover_url': book.cover_url if book.cover_url else None,
            'cover_color': book.cover_color,
        }
        card.update(extra)
        return card

    @staticmethod
    def _compute_favorite_genre(books):
        genres = [b.genre for b in books if b.genre]
        if not genres:
            return None
        counts = Counter(genres)
        top_two = counts.most_common(2)
        # Tie → null
        if len(top_two) > 1 and top_two[0][1] == top_two[1][1]:
            return None
        return top_two[0][0]

    def _compute_longest_book(self, books):
        longest = (
            books.filter(page_count__isnull=False)
            .order_by('-page_count')
            .first()
        )
        if not longest:
            return None
        return self._book_card(longest, page_count=longest.page_count)

    def _compute_most_quoted_book(self, books):
        quoted = (
            books.filter(notes__entry_type='quote')
            .annotate(quote_count=Count('notes'))
            .order_by('-quote_count')
            .first()
        )
        if not quoted:
            return None
        return self._book_card(quoted, quote_count=quoted.quote_count)

    @staticmethod
    def _compute_reading_streak(books):
        months = set()
        for b in books:
            if b.date_finished:
                months.add(b.date_finished.month)

        if not months:
            return 0

        sorted_months = sorted(months)
        best = 1
        current = 1
        for i in range(1, len(sorted_months)):
            if sorted_months[i] == sorted_months[i - 1] + 1:
                current += 1
                best = max(best, current)
            else:
                current = 1
        return best
