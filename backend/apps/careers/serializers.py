from rest_framework import serializers
from rest_framework.reverse import reverse

from apps.engagement.serializers import AuthorSerializer

from .models import Application, Company, CompanyMember, Job


class CompanySerializer(serializers.ModelSerializer):
    open_jobs = serializers.IntegerField(read_only=True, default=0)
    follower_count = serializers.IntegerField(read_only=True, default=0)
    my_role = serializers.CharField(read_only=True, default=None, allow_null=True)
    following = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Company
        fields = [
            "id",
            "slug",
            "name",
            "website",
            "location",
            "industry",
            "size",
            "description",
            "logo",
            "open_jobs",
            "follower_count",
            "my_role",
            "following",
        ]
        read_only_fields = ["slug", "logo"]


class CompanyRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["slug", "name", "logo", "location"]


class MemberSerializer(serializers.ModelSerializer):
    person = AuthorSerializer(source="user")
    user_id = serializers.IntegerField()

    class Meta:
        model = CompanyMember
        fields = ["user_id", "person", "role"]


class AddMemberSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.ChoiceField(choices=CompanyMember.Role.choices)


class SkillNamesField(serializers.ListField):
    """Written as names; read back from the related skills."""

    def to_representation(self, value):
        return [skill.name for skill in value.all()]


class JobSerializer(serializers.ModelSerializer):
    company = CompanyRefSerializer(read_only=True)
    company_slug = serializers.SlugField(write_only=True, required=False)
    skills = SkillNamesField(
        child=serializers.CharField(max_length=80), required=False, max_length=20
    )
    matching_skills = serializers.IntegerField(read_only=True, default=0)
    skill_count = serializers.IntegerField(read_only=True, default=0)
    saved = serializers.BooleanField(read_only=True, default=False)
    my_application = serializers.CharField(read_only=True, default=None, allow_null=True)
    my_application_id = serializers.IntegerField(read_only=True, default=None, allow_null=True)
    applicant_count = serializers.SerializerMethodField()
    on_team = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Job
        fields = [
            "id",
            "company",
            "company_slug",
            "title",
            "description",
            "location",
            "workplace",
            "employment_type",
            "level",
            "salary_min",
            "salary_max",
            "currency",
            "skills",
            "status",
            "published_at",
            "closes_on",
            "created_at",
            "matching_skills",
            "skill_count",
            "saved",
            "my_application",
            "my_application_id",
            "applicant_count",
            "on_team",
        ]
        read_only_fields = ["status", "published_at"]

    def get_applicant_count(self, obj) -> int | None:
        """Only the hiring team sees how many people applied."""
        return getattr(obj, "applicant_count", None) if getattr(obj, "on_team", False) else None

    def validate(self, attrs):
        low = attrs.get("salary_min", getattr(self.instance, "salary_min", None))
        high = attrs.get("salary_max", getattr(self.instance, "salary_max", None))
        if low is not None and high is not None and high < low:
            raise serializers.ValidationError(
                {"salary_max": "The top of the band is below the bottom."}
            )
        if (low or high) and not attrs.get("currency", getattr(self.instance, "currency", "")):
            raise serializers.ValidationError({"currency": "Say which currency the salary is in."})
        return attrs


class ApplicationSerializer(serializers.ModelSerializer):
    applicant = AuthorSerializer(read_only=True)
    applicant_headline = serializers.CharField(source="applicant.profile.headline", default="")
    job = serializers.SerializerMethodField()
    resume_url = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "applicant",
            "applicant_headline",
            "cover_letter",
            "status",
            "status_label",
            "status_changed_at",
            "created_at",
            "resume_url",
        ]

    def get_job(self, obj) -> dict:
        return {
            "id": obj.job_id,
            "title": obj.job.title,
            "company": CompanyRefSerializer(obj.job.company, context=self.context).data,
        }

    def get_resume_url(self, obj) -> str:
        # Served through a permission-checked view, never as a public media URL.
        return reverse("application-resume", args=[obj.pk])


class ApplySerializer(serializers.Serializer):
    resume = serializers.FileField()
    cover_letter = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class StatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[c for c in Application.Status.choices if c[0] != Application.Status.WITHDRAWN]
    )
