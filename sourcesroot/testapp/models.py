from django.db import models
from django.utils import timezone
import secrets

class Participant(models.Model):
    id = models.AutoField(primary_key=True)
    participant_id = models.CharField(max_length=100)
    session_number = models.CharField(max_length=50)
    registration_date = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    session_token = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ["participant_id", "session_number"]

    def save(self, *args, **kwargs):
        if not self.session_token:
            self.session_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.participant_id} - Сессия {self.session_number}"


class ExperimentSession(models.Model):
    id = models.AutoField(primary_key=True)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        default="started",
        choices=[
            ("started", "Начата"),
            ("completed", "Завершена"),
        ],
    )

    def __str__(self):
        return f"Сессия #{self.id} - {self.participant}"


class ExperimentBlock(models.Model):
    id = models.AutoField(primary_key=True)
    experiment_session = models.ForeignKey(ExperimentSession, on_delete=models.CASCADE)
    block_number = models.IntegerField(default=1)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["experiment_session", "block_number"]

    def __str__(self):
        return f"Блок #{self.id} - Сессия {self.experiment_session.id if self.experiment_session else 'N/A'}"


class TrialData(models.Model):
    id = models.AutoField(primary_key=True)
    experiment_block = models.ForeignKey(ExperimentBlock, on_delete=models.CASCADE)
    trial_number = models.IntegerField()

    stimulus = models.TextField(blank=True, null=True)
    response = models.CharField(max_length=500, blank=True, null=True)
    correct_response = models.CharField(max_length=500, blank=True, null=True)
    is_correct = models.BooleanField(null=True, blank=True)
    reaction_time = models.FloatField(null=True, blank=True)

    client_start_time = models.BigIntegerField()
    client_stimulus_time = models.BigIntegerField(null=True, blank=True)
    client_response_time = models.BigIntegerField(null=True, blank=True)

    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["experiment_block", "trial_number"]

    def save(self, *args, **kwargs):
        if self.client_stimulus_time and self.client_response_time and not self.reaction_time:
            self.reaction_time = float(self.client_response_time - self.client_stimulus_time)
        if self.response and self.correct_response and self.is_correct is None:
            self.is_correct = self.response == self.correct_response
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Трайл #{self.trial_number} (RT: {self.reaction_time}ms)"


class NBackTrialData(models.Model):
    id = models.AutoField(primary_key=True)
    experiment_block = models.ForeignKey(ExperimentBlock, on_delete=models.CASCADE)
    trial_number = models.IntegerField()

    stimulus = models.TextField(blank=True, null=True)
    response = models.CharField(max_length=500, blank=True, null=True)
    correct_response = models.CharField(max_length=500, blank=True, null=True)
    is_correct = models.BooleanField(null=True, blank=True)
    reaction_time = models.FloatField(null=True, blank=True)

    client_start_time = models.BigIntegerField()
    client_stimulus_time = models.BigIntegerField(null=True, blank=True)
    client_response_time = models.BigIntegerField(null=True, blank=True)
    client_fixation_time = models.BigIntegerField(null=True, blank=True)

    received_at = models.DateTimeField(auto_now_add=True)

    n_level = models.IntegerField(default=1)
    is_target = models.BooleanField(default=False)
    is_false_alarm = models.BooleanField(default=False, null=True, blank=True)   # исправлено
    is_miss = models.BooleanField(default=False, null=True, blank=True)           # исправлено
    is_correct_rejection = models.BooleanField(default=False, null=True, blank=True) # исправлено
    is_hit = models.BooleanField(default=False, null=True, blank=True)            # исправлено

    stimulus_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ("letter", "Буква"),
            ("position", "Позиция"),
            ("audio", "Аудио"),
            ("visual", "Визуальный"),
        ],
    )
    stimulus_sequence_number = models.IntegerField(null=True, blank=True)
    responded = models.BooleanField(default=False)
    pre_stimulus_delay = models.FloatField(null=True, blank=True)
    stimulus_to_fixation_delay = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Данные N-back триала"
        verbose_name_plural = "Данные N-back триалов"
        db_table = "nback_trial_data"
        unique_together = ["experiment_block", "trial_number"]
        indexes = [
            models.Index(fields=["n_level"]),
            models.Index(fields=["is_target"]),
            models.Index(fields=["is_correct"]),
            models.Index(fields=["responded"]),
        ]

    def save(self, *args, **kwargs):
        # Вычисляем время реакции
        if self.client_stimulus_time and self.client_response_time and not self.reaction_time:
            self.reaction_time = float(self.client_response_time - self.client_stimulus_time)

        # Вычисляем правильность ответа
        if self.response and self.correct_response and self.is_correct is None:
            self.is_correct = self.response == self.correct_response

        self.responded = bool(self.response and self.response.strip())

        # Вычисляем метрики (исходные вычисления)
        # miss
        if self.is_target and not self.responded:
            self.is_miss = True
        else:
            self.is_miss = False

        # correct rejection
        if not self.is_target and not self.responded:
            self.is_correct_rejection = True
        else:
            self.is_correct_rejection = False

        # hit
        if self.is_target and self.is_correct:
            self.is_hit = True
        else:
            self.is_hit = False

        # false alarm
        if not self.is_target and self.responded:
            self.is_false_alarm = True
        else:
            self.is_false_alarm = False

        # Защита от None (на случай, если что-то пошло не так)
        for field in ['is_hit', 'is_miss', 'is_false_alarm', 'is_correct_rejection']:
            if getattr(self, field) is None:
                setattr(self, field, False)

        # Вычисляем задержки
        if self.client_start_time and self.client_stimulus_time:
            self.pre_stimulus_delay = float(self.client_stimulus_time - self.client_start_time)
        if self.client_stimulus_time and self.client_fixation_time:
            self.stimulus_to_fixation_delay = float(self.client_fixation_time - self.client_stimulus_time)

        super().save(*args, **kwargs)

    def __str__(self):
        return (f"N-back (N={self.n_level}) - Триал #{self.trial_number} - "
                f"{'Target' if self.is_target else 'Non-target'} - "
                f"{'Hit' if self.is_hit else 'Miss' if self.is_miss else 'Correct Rejection' if self.is_correct_rejection else 'False Alarm'}")


class GoNoGoTrialData(models.Model):
    id = models.AutoField(primary_key=True)
    experiment_block = models.ForeignKey(ExperimentBlock, on_delete=models.CASCADE)
    trial_number = models.IntegerField()

    level = models.IntegerField()
    category_index = models.IntegerField()
    category_name = models.CharField(max_length=200)
    trial_in_category = models.IntegerField()

    stimulus = models.TextField()
    response = models.CharField(max_length=10, blank=True, null=True)
    correct_response = models.CharField(max_length=10)
    is_correct = models.BooleanField(null=True, blank=True)
    is_target = models.BooleanField()

    reaction_time = models.FloatField(null=True, blank=True)

    client_category_time = models.BigIntegerField()
    client_stimulus_time = models.BigIntegerField()
    client_response_time = models.BigIntegerField(null=True, blank=True)

    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Данные Go/NoGo триала"
        verbose_name_plural = "Данные Go/NoGo триалов"
        db_table = "gonogo_trial_data"
        unique_together = ["experiment_block", "trial_number"]
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["is_target"]),
            models.Index(fields=["is_correct"]),
        ]

    def save(self, *args, **kwargs):
        if self.response and self.correct_response and self.is_correct is None:
            self.is_correct = (self.response == self.correct_response)
        # Если всё же is_correct остался None, установим False
        if self.is_correct is None:
            self.is_correct = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Go/NoGo (уровень {self.level}) - триал #{self.trial_number} - {self.stimulus}"


class QuestionnaireTrialData(models.Model):
    id = models.AutoField(primary_key=True)
    experiment_block = models.ForeignKey(ExperimentBlock, on_delete=models.CASCADE)
    trial_number = models.IntegerField()
    question_text = models.TextField()
    response_value = models.IntegerField()
    reaction_time = models.FloatField(null=True, blank=True)
    client_time = models.BigIntegerField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Данные опросника"
        verbose_name_plural = "Данные опросников"
        db_table = "questionnaire_trial_data"
        unique_together = ["experiment_block", "trial_number"]
        indexes = [
            models.Index(fields=["experiment_block"]),
        ]

    def __str__(self):
        return f"Опросник (блок {self.experiment_block_id}) - вопрос #{self.trial_number}"