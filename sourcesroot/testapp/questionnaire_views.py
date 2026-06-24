from rest_framework import status
from .views import BaseAPIView
from .serializers import BatchQuestionnaireTrialDataSerializer


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