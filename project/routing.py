# project/routing.py
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from activity.consumers import ActivityConsumer, ReactionConsumer, ShareConsumer
from profiles.consumers import ProfileConsumer
from messaging.consumers import ChatConsumer
from notifications.consumers import NotificationConsumer
from posts.consumers import PostConsumer, CommentConsumer
from jobs.consumers import JobListingConsumer, JobApplicationConsumer
from groups.consumers import GroupConsumer, GroupMembershipConsumer
from followers.consumers import FollowerConsumer, FollowRequestConsumer
from events.consumers import EventConsumer
from courses.consumers import CourseConsumer, CourseEnrollmentConsumer, CourseCompletionConsumer
from connections.consumers import ConnectionConsumer, ConnectionRequestConsumer, RecommendationConsumer
from companies.consumers import CompanyConsumer, CompanyUpdateConsumer
from certifications.consumers import CertificationConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/profiles/", ProfileConsumer.as_asgi()),
            path("ws/messaging/", ChatConsumer.as_asgi()),
            path("ws/notifications/$", NotificationConsumer.as_asgi()),
            path("ws/posts/", PostConsumer.as_asgi()),
            path("ws/comments/", CommentConsumer.as_asgi()),
            path("ws/reactions/", ReactionConsumer.as_asgi()),
            path("ws/shares/", ShareConsumer.as_asgi()),
            path("ws/jobs/listings/", JobListingConsumer.as_asgi()),
            path("ws/jobs/applications/", JobApplicationConsumer.as_asgi()),
            path("ws/groups/", GroupConsumer.as_asgi()),
            path("ws/groups/memberships/", GroupMembershipConsumer.as_asgi()),
            path("ws/followers/", FollowerConsumer.as_asgi()),
            path("ws/follow_requests/", FollowRequestConsumer.as_asgi()),
            path("ws/events/", EventConsumer.as_asgi()),
            path("ws/courses/", CourseConsumer.as_asgi()),
            path("ws/courses/enrollments/", CourseEnrollmentConsumer.as_asgi()),
            path("ws/courses/completions/", CourseCompletionConsumer.as_asgi()),
            path("ws/connections/", ConnectionConsumer.as_asgi()),
            path("ws/connection_requests/", ConnectionRequestConsumer.as_asgi()),
            path("ws/recommendations/", RecommendationConsumer.as_asgi()),
            path("ws/companies/", CompanyConsumer.as_asgi()),
            path("ws/company_updates/", CompanyUpdateConsumer.as_asgi()),
            path("ws/certifications/", CertificationConsumer.as_asgi()),
            path("ws/activity/", ActivityConsumer.as_asgi()),
        ])
    ),
})