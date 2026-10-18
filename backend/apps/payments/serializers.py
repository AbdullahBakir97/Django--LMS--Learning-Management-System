from rest_framework import serializers


class RevenueSerializer(serializers.Serializer):
    """One currency: paid orders net of refunds, in cents."""

    currency = serializers.CharField()
    total_cents = serializers.IntegerField()
    recent_cents = serializers.IntegerField(help_text="The last 30 days.")
    orders = serializers.IntegerField()
