from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors, services
from .analytics import course_analytics
from .models import Certificate, Course, Enrollment, Lesson, LessonAttachment, Quiz
from .permissions import IsCourseOwner, IsInstructorOrReadOnly
from .serializers import (
    CertificateSerializer,
    CourseAnalyticsSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    EnrollmentSerializer,
    LessonAttachmentSerializer,
    LessonSerializer,
    ProgressSerializer,
    QuizAttemptSerializer,
    QuizAuthorSerializer,
    QuizPublicSerializer,
    QuizSubmitSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    """Published courses for everyone signed in; drafts only for their instructor."""

    queryset = Course.objects.none()  # for the schema; get_queryset() scopes to the user

    permission_classes = [IsInstructorOrReadOnly, IsCourseOwner]
    lookup_field = "slug"
    filterset_fields = ["level", "language", "status", "instructor"]
    search_fields = ["title", "summary"]
    ordering_fields = ["published_at", "created_at", "title"]

    def get_queryset(self):
        return selectors.course_with_lessons(self.request.user)

    def get_serializer_class(self):
        return CourseListSerializer if self.action == "list" else CourseDetailSerializer

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    @extend_schema(request=None, responses=CourseDetailSerializer)
    @action(detail=True, methods=["post"])
    def publish(self, request, slug=None):
        course = services.publish_course(request.user, self.get_object())
        return Response(CourseDetailSerializer(self.get_queryset().get(pk=course.pk)).data)

    @extend_schema(request=None, responses={201: ProgressSerializer})
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, slug=None):
        enrollment = services.enroll(request.user, self.get_object())
        return Response(ProgressSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: ProgressSerializer, 204: None})
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def progress(self, request, slug=None):
        enrollment = selectors.enrollment_for(request.user, self.get_object())
        if enrollment is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(ProgressSerializer(enrollment).data)

    @extend_schema(responses=CourseAnalyticsSerializer)
    @action(detail=True, methods=["get"])
    def analytics(self, request, slug=None):
        """For the course's instructor (and admins): enrolments, drop-off, quizzes, stalled."""
        course = self.get_object()
        if course.instructor_id != request.user.id and request.user.role != "admin":
            raise PermissionDenied("Only the course's instructor sees its analytics.")
        return Response(CourseAnalyticsSerializer(course_analytics(course)).data)


@extend_schema(parameters=[OpenApiParameter("course_slug", str, OpenApiParameter.PATH)])
class LessonViewSet(viewsets.ModelViewSet):
    """Nested under a course. Content is gated: enrolled, free preview, or the instructor."""

    queryset = Lesson.objects.none()  # for the schema; get_queryset() scopes to the user

    serializer_class = LessonSerializer
    permission_classes = [IsInstructorOrReadOnly, IsCourseOwner]
    pagination_class = None

    def get_course(self):
        return get_object_or_404(
            selectors.visible_courses(self.request.user), slug=self.kwargs["course_slug"]
        )

    def get_queryset(self):
        return (
            Lesson.objects.filter(
                course__slug=self.kwargs["course_slug"],
                course__in=selectors.visible_courses(self.request.user).values("pk"),
            )
            .select_related("course", "quiz")
            .prefetch_related("attachments")
        )

    def retrieve(self, request, *args, **kwargs):
        lesson = self.get_object()
        enrollment = selectors.enrollment_for(request.user, lesson.course)
        if not selectors.can_view_lesson(request.user, lesson, enrollment):
            raise PermissionDenied("Enrol to open this lesson.")
        return Response(self.get_serializer(lesson).data)

    def perform_create(self, serializer):
        course = self.get_course()
        self.check_object_permissions(self.request, course)
        self._check_order(course, serializer.validated_data.get("order"))
        serializer.save(course=course)

    def perform_update(self, serializer):
        lesson = serializer.instance
        self._check_order(lesson.course, serializer.validated_data.get("order"), exclude=lesson.pk)
        serializer.save()

    @staticmethod
    def _check_order(course, order, exclude=None):
        if (
            order is not None
            and Lesson.objects.filter(course=course, order=order).exclude(pk=exclude).exists()
        ):
            raise ValidationError({"order": "Another lesson already has this position."})

    @extend_schema(request=None, responses=ProgressSerializer)
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, course_slug=None, pk=None):
        enrollment = services.complete_lesson(request.user, self.get_object())
        return Response(
            ProgressSerializer(selectors.enrollment_for(request.user, enrollment.course)).data
        )

    @extend_schema(request=LessonAttachmentSerializer, responses={201: LessonAttachmentSerializer})
    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def attachments(self, request, course_slug=None, pk=None):
        lesson = self.get_object()
        serializer = LessonAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(lesson=lesson)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LessonAttachmentDeleteView(generics.DestroyAPIView):
    permission_classes = [IsInstructorOrReadOnly, IsCourseOwner]
    course_attr = "course"
    serializer_class = LessonAttachmentSerializer

    def get_object(self):
        attachment = get_object_or_404(
            LessonAttachment.objects.select_related("lesson__course"), pk=self.kwargs["pk"]
        )
        self.check_object_permissions(self.request, attachment.lesson)
        return attachment


class QuizView(APIView):
    """GET the quiz (answers hidden) if you may see the lesson; PUT the whole quiz as instructor."""

    def _lesson(self, pk):
        return get_object_or_404(Lesson.objects.select_related("course"), pk=pk)

    @extend_schema(responses=QuizPublicSerializer)
    def get(self, request, pk):
        lesson = self._lesson(pk)
        enrollment = selectors.enrollment_for(request.user, lesson.course)
        if not selectors.can_view_lesson(request.user, lesson, enrollment):
            raise PermissionDenied("Enrol to open this quiz.")
        quiz = get_object_or_404(Quiz, lesson=lesson)
        if lesson.course.instructor_id == request.user.id:
            return Response(QuizAuthorSerializer(quiz).data)
        return Response(QuizPublicSerializer(quiz).data)

    @extend_schema(request=QuizAuthorSerializer, responses=QuizAuthorSerializer)
    def put(self, request, pk):
        lesson = self._lesson(pk)
        if not IsCourseOwner().has_object_permission(request, self, lesson):
            raise PermissionDenied()
        quiz = Quiz.objects.filter(lesson=lesson).first()
        serializer = QuizAuthorSerializer(quiz, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(lesson=lesson)
        return Response(
            serializer.data, status=status.HTTP_200_OK if quiz else status.HTTP_201_CREATED
        )

    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        lesson = self._lesson(pk)
        if not IsCourseOwner().has_object_permission(request, self, lesson):
            raise PermissionDenied()
        Quiz.objects.filter(lesson=lesson).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuizSubmitView(APIView):
    @extend_schema(request=QuizSubmitSerializer, responses={201: QuizAttemptSerializer})
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz.objects.select_related("lesson__course"), lesson_id=pk)
        data = QuizSubmitSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        attempt = services.submit_quiz(request.user, quiz, data.validated_data["answers"])
        return Response(QuizAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class MyEnrollmentsView(generics.ListAPIView):
    queryset = Enrollment.objects.none()  # for the schema; get_queryset() scopes to the user
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user).select_related(
            "course__instructor"
        )


class CertificateVerifyView(generics.RetrieveAPIView):
    """Public: anyone with the code can check who completed what."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CertificateSerializer
    lookup_field = "code"
    queryset = Certificate.objects.select_related(
        "enrollment__student", "enrollment__course__instructor"
    )
