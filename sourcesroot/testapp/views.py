from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from typing import Dict, Any, Optional, List

from .models import (
    Participant,
    ExperimentSession,
    ExperimentBlock,
    TrialData,
)
from .serializers import (
    ParticipantSerializer,
    BatchTrialDataSerializer,
)


class BaseAPIView(APIView):
    @staticmethod
    def create_response(data: Dict[str, Any], status_code: int = status.HTTP_200_OK) -> Response:
        return Response(data, status=status_code)

    @staticmethod
    def create_error_response(message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
        return Response({"error": message}, status=status_code)

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Optional[Response]:
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return BaseAPIView.create_error_response(
                f"Необходимо указать: {', '.join(missing_fields)}",
                status.HTTP_400_BAD_REQUEST,
            )
        return None


class BaseCreateOrUpdateView(BaseAPIView):
    model = None
    lookup_field = "id"

    def get_or_create_object(self, **kwargs):
        try:
            return self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            return None


@csrf_exempt
def health_check(request):
    return JsonResponse(
        {
            "status": "healthy",
            "service": "experiment-api",
            "timestamp": timezone.now().isoformat(),
            "endpoints": [
                "/api/register/",
                "/api/session/start/",
                "/api/block/create/",
                "/api/trials/batch/",
                "/api/block/complete/",
                "/api/session/complete/",
                "/api/nback/trials/batch/",
                "/api/gonogo/trials/batch/",
                "/api/questionnaire/trials/batch/",
            ],
        }
    )


class RegisterParticipantView(BaseCreateOrUpdateView):
    serializer_class = ParticipantSerializer
    permission_classes = [AllowAny]
    model = Participant

    def post(self, request):
        try:
            participant_id = request.data.get("participant_id")
            session_number = request.data.get("session_number")

            validation_error = self.validate_required_fields(
                request.data, ["participant_id", "session_number"]
            )
            if validation_error:
                return validation_error

            existing = self.get_or_create_object(
                participant_id=participant_id, session_number=session_number
            )
            if existing:
                return self.create_response(
                    {
                        "message": "Участник уже зарегистрирован",
                        "participant_id": existing.id,
                        "session_token": existing.session_token,
                    }
                )

            participant = Participant.objects.create(
                participant_id=participant_id, session_number=session_number
            )
            return self.create_response(
                {
                    "message": "Регистрация успешна",
                    "participant_id": participant.id,
                    "session_token": participant.session_token,
                },
                status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.create_error_response(str(e))


class StartExperimentSessionView(BaseAPIView):
    def post(self, request):
        validation_error = self.validate_required_fields(request.data, ["participant_id"])
        if validation_error:
            return validation_error

        participant = get_object_or_404(Participant, id=request.data.get("participant_id"))
        session = ExperimentSession.objects.create(participant=participant)

        return self.create_response(
            {
                "session_id": session.id,
                "started_at": session.started_at,
            },
            status.HTTP_201_CREATED,
        )


class CreateExperimentBlockView(BaseAPIView):
    def post(self, request):
        validation_error = self.validate_required_fields(request.data, ["session_id"])
        if validation_error:
            return validation_error

        session = get_object_or_404(ExperimentSession, id=request.data.get("session_id"))
        block_number = request.data.get("block_number", 1)

        existing_block = ExperimentBlock.objects.filter(
            experiment_session=session, block_number=block_number
        ).first()
        if existing_block:
            return self.create_response(
                {
                    "message": "Блок с таким номером уже существует",
                    "block_id": existing_block.id,
                }
            )

        block = ExperimentBlock.objects.create(
            experiment_session=session, block_number=block_number
        )
        return self.create_response(
            {
                "block_id": block.id,
                "started_at": block.started_at,
            },
            status.HTTP_201_CREATED,
        )


class BatchSaveTrialDataView(BaseAPIView):
    def post(self, request):
        serializer = BatchTrialDataSerializer(data=request.data)

        if not serializer.is_valid():
            return self.create_response(
                {"errors": serializer.errors}, status.HTTP_400_BAD_REQUEST
            )

        try:
            trials = serializer.save()
            return self.create_response(
                {
                    "message": "Данные успешно сохранены",
                    "saved_count": len(trials),
                },
                status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.create_error_response(f"Ошибка сохранения: {str(e)}")


class CompleteExperimentBlockView(BaseAPIView):
    def post(self, request):
        validation_error = self.validate_required_fields(request.data, ["block_id"])
        if validation_error:
            return validation_error

        block = get_object_or_404(ExperimentBlock, id=request.data.get("block_id"))
        block.completed_at = timezone.now()
        block.save()

        trial_count = TrialData.objects.filter(experiment_block=block).count()

        return self.create_response(
            {
                "block_id": block.id,
                "completed_at": block.completed_at,
                "trials_count": trial_count,
            }
        )


class CompleteExperimentSessionView(BaseAPIView):
    def post(self, request):
        validation_error = self.validate_required_fields(request.data, ["session_id"])
        if validation_error:
            return validation_error

        session = get_object_or_404(ExperimentSession, id=request.data.get("session_id"))
        session.completed_at = timezone.now()
        session.status = "completed"
        session.save()

        return self.create_response(
            {
                "session_id": session.id,
                "completed_at": session.completed_at,
            }
        )