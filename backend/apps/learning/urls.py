from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

from . import views

router = SimpleRouter()
router.register("courses", views.CourseViewSet, basename="course")
lessons = NestedSimpleRouter(router, "courses", lookup="course")
lessons.register("lessons", views.LessonViewSet, basename="course-lesson")

urlpatterns = [
    path("lessons/<int:pk>/quiz/", views.QuizView.as_view(), name="lesson-quiz"),
    path(
        "lessons/<int:pk>/quiz/submit/", views.QuizSubmitView.as_view(), name="lesson-quiz-submit"
    ),
    path(
        "attachments/<int:pk>/",
        views.LessonAttachmentDeleteView.as_view(),
        name="attachment-delete",
    ),
    path("me/enrollments/", views.MyEnrollmentsView.as_view(), name="my-enrollments"),
    path(
        "certificates/<uuid:code>/",
        views.CertificateVerifyView.as_view(),
        name="certificate-verify",
    ),
    *router.urls,
    *lessons.urls,
]
