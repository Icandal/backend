from rest_framework import serializers
from .models import ExperimentBlock, NBackTrialData


class NBackTrialDataSerializer(serializers.ModelSerializer):
    experiment_block_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = NBackTrialData
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
            "client_response_time",
            "client_fixation_time",
            "received_at",
            "n_level",
            "is_target",
            "is_false_alarm",
            "is_miss",
            "is_correct_rejection",
            "is_hit",
            "stimulus_type",
            "stimulus_sequence_number",
            "responded",
            "pre_stimulus_delay",
            "stimulus_to_fixation_delay",
        ]
        read_only_fields = [
            "id",
            "received_at",
            "is_false_alarm",
            "is_miss",
            "is_correct_rejection",
            "is_hit",
            "responded",
            "pre_stimulus_delay",
            "stimulus_to_fixation_delay",
            "is_correct",
            "reaction_time",
        ]
        extra_kwargs = {
            "trial_number": {"required": True},
            "stimulus": {"required": True},
            "is_target": {"required": True},
            "n_level": {"required": False, "default": 1},
            "stimulus_type": {"required": False, "default": "letter"},
            "response": {"required": False, "allow_blank": True, "allow_null": True},
            "correct_response": {"required": False, "allow_blank": True, "allow_null": True},
            "client_start_time": {"required": False, "allow_null": True},
            "client_stimulus_time": {"required": False, "allow_null": True},
            "client_response_time": {"required": False, "allow_null": True},
            "client_fixation_time": {"required": False, "allow_null": True},
            "stimulus_sequence_number": {"required": False, "allow_null": True},
        }

    def validate(self, data):
        if data.get("is_target") and not data.get("correct_response"):
            data["correct_response"] = "target"
        return data

    def create(self, validated_data):
        experiment_block_id = validated_data.pop("experiment_block_id", None)
        if experiment_block_id is None:
            raise serializers.ValidationError({"experiment_block_id": "Это поле обязательно для создания триала."})

        try:
            experiment_block = ExperimentBlock.objects.get(id=experiment_block_id)
        except ExperimentBlock.DoesNotExist:
            raise serializers.ValidationError({"experiment_block_id": f"Блок с id {experiment_block_id} не существует."})

        validated_data["experiment_block"] = experiment_block
        return NBackTrialData.objects.create(**validated_data)


class BatchNBackTrialDataSerializer(serializers.Serializer):
    trials = NBackTrialDataSerializer(many=True)
    block_id = serializers.IntegerField(required=True)
    n_level = serializers.IntegerField(required=False, default=1)

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
        experiment_block = self.get_experiment_block(block_id)

        trials = []
        seen_trial_numbers = set()

        for trial_data in trials_data:
            trial_number = trial_data.get("trial_number")
            if trial_number is None:
                continue
            if trial_number in seen_trial_numbers:
                continue
            seen_trial_numbers.add(trial_number)

            self._delete_existing_trial(experiment_block, trial_number)

            trial_data = trial_data.copy()
            trial_data["experiment_block_id"] = experiment_block.id

            trial = self._create_single_trial(trial_data)
            if trial:
                trials.append(trial)

        return trials

    @staticmethod
    def _delete_existing_trial(block, trial_number):
        try:
            existing = NBackTrialData.objects.get(experiment_block=block, trial_number=trial_number)
            existing.delete()
        except NBackTrialData.DoesNotExist:
            pass

    @staticmethod
    def _create_single_trial(trial_data):
        serializer = NBackTrialDataSerializer(data=trial_data)
        if serializer.is_valid():
            return serializer.save()
        return None

    @staticmethod
    def get_experiment_block(block_id):
        try:
            return ExperimentBlock.objects.get(id=block_id)
        except ExperimentBlock.DoesNotExist:
            raise serializers.ValidationError(f"ExperimentBlock with id {block_id} does not exist")