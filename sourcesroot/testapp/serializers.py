from rest_framework import serializers
from .models import (
    Participant,
    TrialData,
    GoNoGoTrialData,
    QuestionnaireTrialData
)


class BaseModelSerializer(serializers.ModelSerializer):
    def get_field_names(self, declared_fields, info):
        fields = super().get_field_names(declared_fields, info)
        if hasattr(self.Meta, "extra_fields"):
            fields = list(fields) + list(self.Meta.extra_fields)
        return fields


class BaseBatchSerializer(serializers.Serializer):
    def validate_block_id(self, block_id):
        if not ExperimentBlock.objects.filter(id=block_id).exists():
            raise serializers.ValidationError(f"ExperimentBlock with id {block_id} does not exist")
        return block_id

    @staticmethod
    def get_experiment_block(block_id):
        try:
            return ExperimentBlock.objects.get(id=block_id)
        except ExperimentBlock.DoesNotExist:
            raise serializers.ValidationError(f"ExperimentBlock with id {block_id} does not exist")


class ParticipantSerializer(BaseModelSerializer):
    class Meta:
        model = Participant
        fields = [
            "id",
            "participant_id",
            "session_number",
            "registration_date",
            "session_token",
        ]


class TrialDataSerializer(BaseModelSerializer):
    class Meta:
        model = TrialData
        fields = [
            "experiment_block",
            "trial_number",
            "stimulus",
            "response",
            "correct_response",
            "is_correct",
            "reaction_time",
            "client_start_time",
            "client_stimulus_time",
            "client_response_time",
            "received_at",
        ]


class BatchTrialDataSerializer(BaseBatchSerializer):
    trials = TrialDataSerializer(many=True)

    def create(self, validated_data):
        trials_data = validated_data["trials"]
        trials = [TrialData.objects.create(**trial_data) for trial_data in trials_data]
        return trials


class GoNoGoTrialDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoNoGoTrialData
        fields = [
            'experiment_block',
            'trial_number',
            'level',
            'category_index',
            'category_name',
            'trial_in_category',
            'stimulus',
            'response',
            'correct_response',
            'is_correct',
            'is_target',
            'reaction_time',
            'client_category_time',
            'client_stimulus_time',
            'client_response_time',
        ]


class BatchGoNoGoTrialDataSerializer(serializers.Serializer):
    trials = GoNoGoTrialDataSerializer(many=True)

    def create(self, validated_data):
        trials_data = validated_data['trials']
        trials = [GoNoGoTrialData.objects.create(**trial_data) for trial_data in trials_data]
        return trials


class QuestionnaireTrialDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionnaireTrialData
        fields = [
            'experiment_block',
            'trial_number',
            'question_text',
            'response_value',
            'reaction_time',
            'client_time',
        ]


class BatchQuestionnaireTrialDataSerializer(serializers.Serializer):
    trials = QuestionnaireTrialDataSerializer(many=True)

    def create(self, validated_data):
        trials_data = validated_data['trials']
        trials = [QuestionnaireTrialData.objects.create(**trial_data) for trial_data in trials_data]
        return trials