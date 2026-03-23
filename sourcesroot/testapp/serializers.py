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


class TrialDataSerializer(serializers.ModelSerializer):
    experiment_block_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = TrialData
        fields = [
            "id",
            "experiment_block_id",
            "trial_number",
            "stimulus",
            "response",
            "correct_response",
            "is_correct",
            "reaction_time",
            "client_start_time",
            "client_stimulus_time",
            "client_fixation_time",
            "client_response_time",
            "received_at",
        ]
        read_only_fields = ["id", "received_at", "is_correct", "reaction_time"]
        extra_kwargs = {
            "trial_number": {"required": True},
            "stimulus": {"required": True},
            "client_start_time": {"required": True},
        }

    def create(self, validated_data):
        experiment_block_id = validated_data.pop("experiment_block_id", None)
        if experiment_block_id is None:
            raise serializers.ValidationError({"experiment_block_id": "Это поле обязательно для создания триала."})
        try:
            experiment_block = ExperimentBlock.objects.get(id=experiment_block_id)
        except ExperimentBlock.DoesNotExist:
            raise serializers.ValidationError({"experiment_block_id": f"Блок с id {experiment_block_id} не существует."})
        validated_data["experiment_block"] = experiment_block
        return TrialData.objects.create(**validated_data)


class BatchTrialDataSerializer(serializers.Serializer):
    trials = TrialDataSerializer(many=True)
    block_id = serializers.IntegerField(required=True)

    def validate(self, data):
        block_id = data.get("block_id")
        if not ExperimentBlock.objects.filter(id=block_id).exists():
            raise serializers.ValidationError({"block_id": f"Блок с id {block_id} не существует."})
        trials = data.get("trials", [])
        if not isinstance(trials, list):
            raise serializers.ValidationError({"trials": "Должен быть массив."})
        if len(trials) == 0:
            raise serializers.ValidationError({"trials": "Массив не может быть пустым."})
        return data

    def create(self, validated_data):
        trials_data = validated_data.pop("trials", [])
        block_id = validated_data["block_id"]
        trials = []
        seen_trial_numbers = set()
        for trial_data in trials_data:
            trial_number = trial_data.get("trial_number")
            if trial_number is None:
                continue
            if trial_number in seen_trial_numbers:
                continue
            seen_trial_numbers.add(trial_number)
            # (опционально)
            TrialData.objects.filter(experiment_block_id=block_id, trial_number=trial_number).delete()
            trial_data["experiment_block_id"] = block_id
            serializer = TrialDataSerializer(data=trial_data)
            if serializer.is_valid():
                trials.append(serializer.save())
        return trials

class GoNoGoTrialDataSerializer(serializers.ModelSerializer):
    experiment_block_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = GoNoGoTrialData
        fields = [
            'id',
            'experiment_block_id',
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
            'received_at',
        ]
        read_only_fields = ['id', 'received_at', 'is_correct']

    def create(self, validated_data):
        experiment_block_id = validated_data.pop("experiment_block_id", None)
        if experiment_block_id is None:
            raise serializers.ValidationError({"experiment_block_id": "Это поле обязательно для создания триала."})
        try:
            experiment_block = ExperimentBlock.objects.get(id=experiment_block_id)
        except ExperimentBlock.DoesNotExist:
            raise serializers.ValidationError({"experiment_block_id": f"Блок с id {experiment_block_id} не существует."})
        validated_data["experiment_block"] = experiment_block
        return GoNoGoTrialData.objects.create(**validated_data)


class BatchGoNoGoTrialDataSerializer(serializers.Serializer):
    trials = GoNoGoTrialDataSerializer(many=True)
    block_id = serializers.IntegerField(required=True)

    def validate(self, data):
        block_id = data.get("block_id")
        if not ExperimentBlock.objects.filter(id=block_id).exists():
            raise serializers.ValidationError({"block_id": f"Блок с id {block_id} не существует."})
        trials = data.get("trials", [])
        if not isinstance(trials, list):
            raise serializers.ValidationError({"trials": "Должен быть массив."})
        if len(trials) == 0:
            raise serializers.ValidationError({"trials": "Массив не может быть пустым."})
        return data

    def create(self, validated_data):
        trials_data = validated_data.pop("trials", [])
        block_id = validated_data["block_id"]
        trials = []
        seen_trial_numbers = set()
        for trial_data in trials_data:
            trial_number = trial_data.get("trial_number")
            if trial_number is None:
                continue
            if trial_number in seen_trial_numbers:
                continue
            seen_trial_numbers.add(trial_number)
            GoNoGoTrialData.objects.filter(experiment_block_id=block_id, trial_number=trial_number).delete()
            trial_data["experiment_block_id"] = block_id
            serializer = GoNoGoTrialDataSerializer(data=trial_data)
            if serializer.is_valid():
                trials.append(serializer.save())
        return trials

class QuestionnaireTrialDataSerializer(serializers.ModelSerializer):
    experiment_block_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = QuestionnaireTrialData
        fields = [
            'id',
            'experiment_block_id',
            'trial_number',
            'question_text',
            'response_value',
            'reaction_time',
            'client_time',
            'received_at',
        ]
        read_only_fields = ['id', 'received_at']

    def create(self, validated_data):
        experiment_block_id = validated_data.pop("experiment_block_id", None)
        if experiment_block_id is None:
            raise serializers.ValidationError({"experiment_block_id": "Это поле обязательно для создания триала."})
        try:
            experiment_block = ExperimentBlock.objects.get(id=experiment_block_id)
        except ExperimentBlock.DoesNotExist:
            raise serializers.ValidationError({"experiment_block_id": f"Блок с id {experiment_block_id} не существует."})
        validated_data["experiment_block"] = experiment_block
        return QuestionnaireTrialData.objects.create(**validated_data)


class BatchQuestionnaireTrialDataSerializer(serializers.Serializer):
    trials = QuestionnaireTrialDataSerializer(many=True)
    block_id = serializers.IntegerField(required=True)

    def validate(self, data):
        block_id = data.get("block_id")
        if not ExperimentBlock.objects.filter(id=block_id).exists():
            raise serializers.ValidationError({"block_id": f"Блок с id {block_id} не существует."})
        trials = data.get("trials", [])
        if not isinstance(trials, list):
            raise serializers.ValidationError({"trials": "Должен быть массив."})
        if len(trials) == 0:
            raise serializers.ValidationError({"trials": "Массив не может быть пустым."})
        return data

    def create(self, validated_data):
        trials_data = validated_data.pop("trials", [])
        block_id = validated_data["block_id"]
        trials = []
        seen_trial_numbers = set()
        for trial_data in trials_data:
            trial_number = trial_data.get("trial_number")
            if trial_number is None:
                continue
            if trial_number in seen_trial_numbers:
                continue
            seen_trial_numbers.add(trial_number)
            QuestionnaireTrialData.objects.filter(experiment_block_id=block_id, trial_number=trial_number).delete()
            trial_data["experiment_block_id"] = block_id
            serializer = QuestionnaireTrialDataSerializer(data=trial_data)
            if serializer.is_valid():
                trials.append(serializer.save())
        return trials