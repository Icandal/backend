from django.urls import path
from . import views, nback_views, gonogo_views, questionnaire_views

urlpatterns = [
    path("register/", views.RegisterParticipantView.as_view(), name="register"),
    path("session/start/", views.StartExperimentSessionView.as_view(), name="start-session"),
    path("block/create/", views.CreateExperimentBlockView.as_view(), name="create-block"),
    path("trials/batch/", views.BatchSaveTrialDataView.as_view(), name="batch-save-trials"),
    path("block/complete/", views.CompleteExperimentBlockView.as_view(), name="complete-block"),
    path("session/complete/", views.CompleteExperimentSessionView.as_view(), name="complete-session"),
    path("health/", views.health_check, name="health-check"),

    path("nback/trials/batch/", nback_views.BatchSaveNBackTrialDataView.as_view(), name="nback-batch-save-trials"),
    path("gonogo/trials/batch/", gonogo_views.BatchSaveGoNoGoTrialDataView.as_view(), name="gonogo-batch-save-trials"),
    path("questionnaire/trials/batch/", questionnaire_views.BatchSaveQuestionnaireTrialDataView.as_view(), name="questionnaire-batch-save-trials"),
]