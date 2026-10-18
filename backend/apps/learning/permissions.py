from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsInstructorOrReadOnly(BasePermission):
    """Anyone signed in may read; only instructors and admins may write."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_instructor


class IsCourseOwner(BasePermission):
    """Object-level: the course's instructor, or an admin. Views set `course_attr`."""

    def has_object_permission(self, request, view, obj):
        course = getattr(obj, getattr(view, "course_attr", "course"), obj)
        return course.instructor_id == request.user.id or request.user.role == "admin"
