from django.core.validators import FileExtensionValidator
from django.urls import reverse
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import (
    Certificate,
    Choice,
    Course,
    Enrollment,
    Lesson,
    LessonAttachment,
    Question,
    Quiz,
)


class LessonSummarySerializer(serializers.ModelSerializer):
    has_quiz = serializers.SerializerMethodField()

    def get_has_quiz(self, lesson) -> bool:
        return hasattr(lesson, "quiz")

    class Meta:
        model = Lesson
        fields = ["id", "title", "order", "is_free_preview", "video_url", "has_quiz"]


class CourseListSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "slug",
            "title",
            "summary",
            "cover",
            "level",
            "language",
            "status",
            "price_cents",
            "currency",
            "published_at",
            "instructor",
            "lesson_count",
            "enrollment_count",
            "created_at",
        ]
        read_only_fields = ["slug", "status", "currency", "published_at", "created_at"]

    def validate_price_cents(self, value):
        # Card networks will not charge less than about 0.50 in most currencies.
        if 0 < value < 50:
            raise serializers.ValidationError("A paid course costs at least 0.50.")
        return value


class CourseDetailSerializer(CourseListSerializer):
    lessons = LessonSummarySerializer(many=True, read_only=True)
    prerequisites = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Course.objects.all(), required=False
    )

    class Meta(CourseListSerializer.Meta):
        fields = [*CourseListSerializer.Meta.fields, "description", "prerequisites", "lessons"]

    def to_representation(self, course):
        data = super().to_representation(course)
        request = self.context.get("request")
        user = request.user if request else None
        open_to_all = user and (
            course.instructor_id == user.id
            or user.role == "admin"
            or course.enrollments.filter(student=user).exists()
        )
        if not open_to_all:  # the outline is public; videos of locked lessons are not
            for lesson in data["lessons"]:
                if not lesson["is_free_preview"]:
                    lesson["video_url"] = ""
        return data


ATTACHMENT_TYPES = "pdf zip png jpg jpeg gif webp txt md csv docx xlsx pptx py ipynb sql".split()
ATTACHMENT_MAX_BYTES = 25 * 1024 * 1024  # under nginx's 40 MB body limit


class LessonAttachmentSerializer(serializers.ModelSerializer):
    # No HTML, SVG or scripts: they would run on the site's own origin if someone opened them.
    file = serializers.FileField(
        write_only=True, validators=[FileExtensionValidator(ATTACHMENT_TYPES)]
    )
    url = serializers.SerializerMethodField(help_text="Download with the access token.")

    class Meta:
        model = LessonAttachment
        fields = ["id", "title", "file", "url"]

    def get_url(self, attachment) -> str:
        return reverse("attachment-file", args=[attachment.pk])

    def validate_file(self, file):
        if file.size > ATTACHMENT_MAX_BYTES:
            raise serializers.ValidationError("Attachments can be up to 25 MB.")
        return file


class LessonSerializer(serializers.ModelSerializer):
    attachments = LessonAttachmentSerializer(many=True, read_only=True)
    has_quiz = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "order",
            "content",
            "video_url",
            "is_free_preview",
            "attachments",
            "has_quiz",
        ]

    def get_has_quiz(self, lesson) -> bool:
        return hasattr(lesson, "quiz")


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]


class ChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "choices"]

    def validate_choices(self, choices):
        if len(choices) < 2:
            raise serializers.ValidationError("A question needs at least two choices.")
        if not any(c["is_correct"] for c in choices):
            raise serializers.ValidationError("Mark at least one choice as correct.")
        return choices


class QuestionPublicSerializer(serializers.ModelSerializer):
    choices = ChoicePublicSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "choices"]


class QuizAuthorSerializer(serializers.ModelSerializer):
    """Instructor view and full replace: PUT the whole quiz with its questions."""

    questions = QuestionSerializer(many=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "pass_score", "questions"]

    def create(self, validated):
        questions = validated.pop("questions")
        quiz = Quiz.objects.create(**validated)
        self._write_questions(quiz, questions)
        return quiz

    def update(self, quiz, validated):
        questions = validated.pop("questions", None)
        for k, v in validated.items():
            setattr(quiz, k, v)
        quiz.save()
        if questions is not None:
            quiz.questions.all().delete()
            self._write_questions(quiz, questions)
        return quiz

    @staticmethod
    def _write_questions(quiz, questions):
        for i, q in enumerate(questions, start=1):
            choices = q.pop("choices")
            question = Question.objects.create(quiz=quiz, order=i, text=q["text"])
            Choice.objects.bulk_create([Choice(question=question, **c) for c in choices])


class QuizPublicSerializer(serializers.ModelSerializer):
    questions = QuestionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "pass_score", "questions"]


class QuizSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.IntegerField(), help_text="question id -> choice id"
    )

    def validate_answers(self, answers):
        try:
            return {int(k): v for k, v in answers.items()}
        except ValueError:
            raise serializers.ValidationError("Keys must be question ids.") from None


class QuizAttemptSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    passed = serializers.BooleanField()
    pass_score = serializers.IntegerField(source="quiz.pass_score")
    created_at = serializers.DateTimeField()


class ProgressSerializer(serializers.ModelSerializer):
    """The signed-in student's standing in a course."""

    completed_lessons = serializers.SerializerMethodField()
    passed_quizzes = serializers.SerializerMethodField()
    certificate_code = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "status",
            "completed_at",
            "completed_lessons",
            "passed_quizzes",
            "certificate_code",
            "created_at",
        ]

    def get_completed_lessons(self, enrollment) -> list[int]:
        return [p.lesson_id for p in enrollment.lesson_progress.all()]

    def get_passed_quizzes(self, enrollment) -> list[int]:
        return sorted({a.quiz_id for a in enrollment.quiz_attempts.all() if a.passed})

    def get_certificate_code(self, enrollment) -> str | None:
        certificate = getattr(enrollment, "certificate", None)
        return str(certificate.code) if certificate else None


class CourseBriefSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)

    class Meta:
        model = Course
        fields = ["id", "slug", "title", "summary", "cover", "level", "instructor"]


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseBriefSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "course", "status", "completed_at", "created_at"]


class CertificateSerializer(serializers.ModelSerializer):
    """Public verification record."""

    student = serializers.SerializerMethodField()
    course = serializers.CharField(source="enrollment.course.title")
    instructor = serializers.SerializerMethodField()
    completed_at = serializers.DateTimeField(source="enrollment.completed_at")

    class Meta:
        model = Certificate
        fields = ["code", "student", "course", "instructor", "completed_at", "pdf"]

    def get_student(self, certificate) -> str:
        user = certificate.enrollment.student
        return user.get_full_name() or user.username

    def get_instructor(self, certificate) -> str:
        user = certificate.enrollment.course.instructor
        return user.get_full_name() or user.username


class WeekCountSerializer(serializers.Serializer):
    week = serializers.DateField()
    count = serializers.IntegerField()


class LessonFunnelSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    order = serializers.IntegerField()
    completed = serializers.IntegerField()


class QuizStatsSerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField()
    title = serializers.CharField()
    learners = serializers.IntegerField()
    attempts = serializers.IntegerField()
    passed = serializers.IntegerField()
    average_score = serializers.IntegerField()


class StalledLearnerSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.CharField()
    lessons_done = serializers.IntegerField()
    last_active = serializers.DateTimeField()


class CourseAnalyticsSerializer(serializers.Serializer):
    enrolled = serializers.IntegerField()
    active = serializers.IntegerField()
    completed = serializers.IntegerField()
    completion_rate = serializers.IntegerField(help_text="Percent of everyone who enrolled")
    average_days_to_complete = serializers.FloatField(allow_null=True)
    lesson_count = serializers.IntegerField()
    weekly_enrolments = WeekCountSerializer(many=True)
    lessons = LessonFunnelSerializer(many=True)
    quizzes = QuizStatsSerializer(many=True)
    stalled_count = serializers.IntegerField()
    stalled = StalledLearnerSerializer(many=True)
