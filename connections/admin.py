from django.contrib import admin
from .models import ConnectionRequest, Connection, Recommendation
from profiles.models import UserProfile

# Inline for Connection in UserProfileAdmin
class ConnectionInline(admin.TabularInline):
    model = Connection
    fk_name = 'user'
    verbose_name_plural = 'Connections'
    readonly_fields = ('created_at',)

# Inline for Recommendation in UserProfileAdmin
class RecommendationInline(admin.TabularInline):
    model = Recommendation
    fk_name = 'recommended_user'
    verbose_name_plural = 'Recommendations'

@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('from_user__user__username', 'to_user__user__username')

    def save_model(self, request, obj, form, change):
        """Override save_model to associate the current user with the ConnectionRequest."""
        if not obj.pk:
            obj.from_user = UserProfile.objects.get(user=request.user)
        obj.save()

@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'connection', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__user__username', 'connection__user__username')

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('recommended_by', 'recommended_user', 'content')
    search_fields = ('recommended_by__user__username', 'recommended_user__user__username')


# Register Inline models in UserProfileAdmin

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'role', 'is_verified')
    list_filter = ('role', 'is_verified')
    search_fields = ('user__username', 'location')

    inlines = [ConnectionInline, RecommendationInline]

    def get_queryset(self, request):
        """Limit queryset to current user's UserProfile."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        """Override save_model to associate the current user with the UserProfile."""
        if not obj.pk:
            obj.user = request.user
        obj.save()

