from rest_framework import status
from rest_framework.permissions import AllowAny

from .serializers import BatchGoNoGoTrialDataSerializer
from .views import BaseAPIView


class BatchSaveGoNoGoTrialDataView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = BatchGoNoGoTrialDataSerializer(data=request.data)

        if not serializer.is_valid():
            return self.create_response(
                {"errors": serializer.errors}, status.HTTP_400_BAD_REQUEST
            )

        try:
            trials = serializer.save()
            return self.create_response(
                {
                    "message": "Данные Go/NoGo успешно сохранены",
                    "saved_count": len(trials),
                },
                status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.create_error_response(f"Ошибка сохранения: {str(e)}")