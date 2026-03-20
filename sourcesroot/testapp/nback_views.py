import logging
from rest_framework import status
from rest_framework.response import Response
from .models import ExperimentBlock, NBackTrialData
from .nback_serializers import BatchNBackTrialDataSerializer
from .views import BaseAPIView

logger = logging.getLogger(__name__)


class BatchSaveNBackTrialDataView(BaseAPIView):
    def post(self, request):
        serializer = BatchNBackTrialDataSerializer(data=request.data)

        if not serializer.is_valid():
            return self.create_response(
                {
                    "errors": serializer.errors,
                },
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            trials = serializer.save()
            saved_count = len(trials)
            total_trials = len(request.data.get("trials", []))

            response_data = {
                "message": "N-back данные успешно сохранены",
                "saved_count": saved_count,
                "block_id": request.data.get("block_id"),
                "n_level": request.data.get("n_level", 1),
            }
            if saved_count < total_trials:
                response_data["warning"] = (
                    f"Сохранено только {saved_count} из {total_trials} триалов. "
                    "Проверьте уникальность trial_number и корректность данных."
                )

            return self.create_response(response_data, status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Ошибка при сохранении N-back данных")
            return self.create_error_response(
                f"Ошибка сохранения N-back данных: {str(e)}",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )