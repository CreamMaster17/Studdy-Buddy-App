from rest_framework import serializers

from .models import Assessment, AssessmentAttempt, ContentItem, Note, Subject
from .services.assessment_services import is_on_track


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "slug"]


class ContentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentItem
        fields = [
            "id", "subject", "title", "content_type", "file",
            "external_url", "description", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        file = attrs.get("file", getattr(self.instance, "file", None))
        url = attrs.get("external_url", getattr(self.instance, "external_url", ""))
        if not file and not url:
            raise serializers.ValidationError("Provide either a file or an external_url.")
        return attrs


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentAttempt
        fields = ["id", "assessment", "score", "taken_at", "passed"]
        read_only_fields = ["taken_at", "passed"]


class AssessmentSerializer(serializers.ModelSerializer):
    on_track = serializers.SerializerMethodField()
    is_due = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            "id", "subject", "title", "frequency", "passing_score",
            "next_due_date", "active", "on_track", "is_due",
        ]

    def get_on_track(self, obj):
        return is_on_track(obj)

    def get_is_due(self, obj):
        return obj.is_due()


# only create and list fields made for now
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "subject", "body", "created_at"]
        read_only_fields = ["created_at"]
