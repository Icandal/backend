from rest_framework import status
from .views import BaseAPIView
from .serializers import (
    BatchQuestionnaireTrialDataSerializer,
    RegisterParticipantSerializer,
)


class BatchSaveQuestionnaireTrialDataView(BaseAPIView):
    def post(self, request):
        serializer = BatchQuestionnaireTrialDataSerializer(data=request.data)
        if not serializer.is_valid():
            return self.create_response(
                {"errors": serializer.errors}, status.HTTP_400_BAD_REQUEST
            )
        try:
            trials = serializer.save()
            return self.create_response(
                {
                    "message": "Данные опросника успешно сохранены",
                    "saved_count": len(trials),
                },
                status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.create_error_response(f"Ошибка сохранения: {str(e)}")


# НОВЫЙ VIEW ДЛЯ РЕГИСТРАЦИИ
class RegisterParticipantView(BaseAPIView):
    def post(self, request):
        serializer = RegisterParticipantSerializer(data=request.data)
        if not serializer.is_valid():
            return self.create_response(
                {"errors": serializer.errors},
                status.HTTP_400_BAD_REQUEST
            )
        try:
            participant = serializer.save()
            return self.create_response(
                {
                    "message": "Участник успешно зарегистрирован",
                    "participant_id": participant.participant_id,
                    "session_number": participant.session_number,
                },
                status.HTTP_201_CREATED
            )
        except Exception as e:
            return self.create_error_response(f"Ошибка регистрации: {str(e)}")