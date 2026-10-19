from rest_framework import serializers


class WeekSerializer(serializers.Serializer):
    week = serializers.DateField()
    count = serializers.IntegerField()


class RevenueSerializer(serializers.Serializer):
    currency = serializers.CharField()
    total_cents = serializers.IntegerField()
    recent_cents = serializers.IntegerField()
    orders = serializers.IntegerField()


class TopCourseSerializer(serializers.Serializer):
    slug = serializers.SlugField()
    title = serializers.CharField()
    instructor = serializers.CharField()
    new_enrolments = serializers.IntegerField()
    enrolled = serializers.IntegerField()


class OverviewSerializer(serializers.Serializer):
    """Counts with `new_` are the last 30 days; revenue is per currency, in cents."""

    people = serializers.IntegerField()
    new_people = serializers.IntegerField()
    courses = serializers.IntegerField()
    enrolments = serializers.IntegerField()
    new_enrolments = serializers.IntegerField()
    completion_rate = serializers.IntegerField()
    posts = serializers.IntegerField(help_text="Posts in the last 30 days.")
    open_jobs = serializers.IntegerField()
    open_reports = serializers.IntegerField(help_text="Distinct reported items waiting for review.")
    revenue = RevenueSerializer(many=True)
    weekly_signups = WeekSerializer(many=True)
    weekly_enrolments = WeekSerializer(many=True)
    top_courses = TopCourseSerializer(many=True)
