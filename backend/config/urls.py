from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from chat import views as chat
from progress import views as progress
from srs import views as srs
from trainer import views as trainer
from vocabulary import views as vocabulary

admin.site.site_header = "PoliglotAi — әдіскер панелі"

api = [
    path("auth/", include("users.urls")),
    path("verbs/", vocabulary.VerbListView.as_view()),
    path("verbs/<int:pk>/forms/", vocabulary.VerbFormsView.as_view()),
    path("course/", vocabulary.CourseView.as_view()),
    path("srs/today/", srs.TodayView.as_view()),
    path("srs/add/", srs.AddWordView.as_view()),
    path("srs/<int:word_id>/answer/", srs.AnswerView.as_view()),
    path("trainer/task/", trainer.TaskView.as_view()),
    path("trainer/check/", trainer.CheckView.as_view()),
    path("progress/", progress.ProgressView.as_view()),
    path("progress/reset/", progress.ResetView.as_view()),
    path("chat/scenarios/", chat.ScenarioListView.as_view()),
    path("chat/conversations/", chat.ConversationListView.as_view()),
    path("chat/conversations/<int:pk>/", chat.ConversationDetailView.as_view()),
    path("chat/conversations/<int:pk>/messages/", chat.SendMessageView.as_view()),
    path("chat/conversations/<int:pk>/summary/", chat.SummaryView.as_view()),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api)),
    path("healthz", lambda request: JsonResponse({"ok": True})),
]
