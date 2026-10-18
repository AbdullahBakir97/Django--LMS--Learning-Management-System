from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Achievement, Education, Experience, PortfolioItem, Profile, ProfileSkill, Skill


class DatedEntrySerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date is before start date."})
        return attrs


class ExperienceSerializer(DatedEntrySerializer):
    class Meta:
        model = Experience
        fields = ["id", "title", "company", "location", "start_date", "end_date", "description"]


class EducationSerializer(DatedEntrySerializer):
    class Meta:
        model = Education
        fields = [
            "id",
            "institution",
            "degree",
            "field_of_study",
            "start_date",
            "end_date",
            "description",
        ]


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]


class ProfileSkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="skill.name", read_only=True)
    endorsement_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProfileSkill
        fields = ["id", "name", "level", "endorsement_count"]


class PortfolioItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioItem
        fields = ["id", "title", "url", "description", "completed_on"]


class AchievementSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="get_code_display", read_only=True)
    earned_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Achievement
        fields = ["code", "title", "earned_at"]


class AddSkillSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80)
    level = serializers.ChoiceField(choices=ProfileSkill.Level.choices, default="intermediate")


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    skills = ProfileSkillSerializer(many=True, read_only=True)
    portfolio = PortfolioItemSerializer(many=True, read_only=True)
    achievements = AchievementSerializer(source="user.achievements", many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "headline",
            "bio",
            "avatar",
            "location",
            "website",
            "experiences",
            "educations",
            "skills",
            "portfolio",
            "achievements",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
