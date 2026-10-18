from rest_framework import serializers

from apps.engagement.serializers import AuthorSerializer

from .models import Report


class ReportCreateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=Report.Kind.choices)
    object_id = serializers.IntegerField(min_value=1)
    reason = serializers.ChoiceField(choices=Report.Reason.choices)
    details = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")


class ReportSerializer(serializers.ModelSerializer):
    reporter = AuthorSerializer(read_only=True)
    reason_label = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = Report
        fields = ["id", "reporter", "reason", "reason_label", "details", "created_at"]


class PreviewSerializer(serializers.Serializer):
    title = serializers.CharField()
    excerpt = serializers.CharField(allow_blank=True)
    url = serializers.CharField(allow_blank=True)
    author = serializers.CharField()


class QueueItemSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=Report.Kind.choices)
    object_id = serializers.IntegerField()
    exists = serializers.BooleanField()
    preview = PreviewSerializer(allow_null=True)
    report_count = serializers.IntegerField()
    reasons = serializers.DictField(child=serializers.IntegerField())
    reports = ReportSerializer(many=True)
    first_reported_at = serializers.DateTimeField()


class ResolveSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["remove", "dismiss"])
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
