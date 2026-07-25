from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Assessment, AssessmentAttempt, ContentItem, Note, Subject

from .serializers import (
    AssessmentAttemptSerializer,
    AssessmentSerializer,
    ContentItemSerializer,
    NoteSerializer,
    SubjectSerializer,
)
from .services.geminiservice import (
    generate_flashcards,
    generate_quiz,
    summarize_notes,
)


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]


class ContentItemViewSet(viewsets.ModelViewSet):
    serializer_class = ContentItemSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["subject", "subject__slug", "content_type"]

    def get_queryset(self):
        return ContentItem.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["subject", "frequency", "active"]

    def get_queryset(self):
        return Assessment.objects.filter(owner=self.request.user).select_related("subject")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def submit_attempt(self, request, pk=None):
        """POST {"score": 85} — records an attempt and advances next_due_date."""
        assessment = self.get_object()
        serializer = AssessmentAttemptSerializer(data={**request.data, "assessment": assessment.id})
        serializer.is_valid(raise_exception=True)
        attempt = serializer.save(assessment=assessment)
        assessment.advance_due_date()
        return Response({
            "attempt": AssessmentAttemptSerializer(attempt).data,
            "on_track": is_on_track(assessment),
            "next_due_date": assessment.next_due_date,
        }, status=201)

    @action(detail=False, methods=["get"])
    def due(self, request):
        """GET assessments currently due for the requesting user."""
        due = [a for a in self.get_queryset() if a.is_due()]
        return Response(AssessmentSerializer(due, many=True).data)


class AssessmentAttemptViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AssessmentAttemptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["assessment"]

    def get_queryset(self):
        return AssessmentAttempt.objects.filter(assessment__owner=self.request.user)


# I will update with update/delete/detail retrieve later.
class NoteViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["subject"]

    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # TODO: retrieve, update, destroy, rich text/markdown, tagging, linking to ContentItem
class StudyToolsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_text(self, request):
        text = request.data.get("text", "")

        if not isinstance(text, str) or not text.strip():
            return None, Response(
                {"error": "A non-empty text field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return text.strip(), None

    @action(detail=False, methods=["post"])
    def summarize(self, request):
        text, error_response = self.get_text(request)

        if error_response:
            return error_response

        try:
            summary = summarize_notes(text)
            return Response({"summary": summary})
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def flashcards(self, request):
        text, error_response = self.get_text(request)

        if error_response:
            return error_response

        try:
            flashcards = generate_flashcards(text)
            return Response({"flashcards": flashcards})
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def quiz(self, request):
        text, error_response = self.get_text(request)

        if error_response:
            return error_response

        try:
            quiz = generate_quiz(text)
            return Response({"quiz": quiz})
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )