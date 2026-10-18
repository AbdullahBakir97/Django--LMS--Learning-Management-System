from django.apps import AppConfig


class CommunityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.community"

    def ready(self):
        from apps.engagement import registry

        from .models import Post
        from .selectors import can_view_post

        registry.register(
            "post",
            Post,
            can_view=can_view_post,
            owner_id=lambda post: post.author_id,
            url=lambda post: f"/posts/{post.pk}",
            title=lambda post: f"“{post.body[:40]}{'…' if len(post.body) > 40 else ''}”",
        )
