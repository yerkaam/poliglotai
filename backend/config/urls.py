from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404, JsonResponse
from django.urls import include, path, re_path

from chat import views as chat
from classroom import views as classroom
from config import monitoring
from progress import views as progress
from srs import views as srs
from trainer import views as trainer
from vocabulary import views as vocabulary

admin.site.site_header = "PoliglotAi — әдіскер панелі"


def client_config(request):
    """Settings the browser app needs at start: the public Sentry DSN (empty turns reporting off)."""
    return JsonResponse(
        {
            "sentry_dsn": settings.SENTRY_FRONTEND_DSN,
            "environment": settings.SENTRY_ENVIRONMENT,
            "release": monitoring.release(),
        }
    )


api = [
    path("config/", client_config),
    path("auth/", include("users.urls")),
    path("verbs/", vocabulary.VerbListView.as_view()),
    path("verbs/<int:pk>/forms/", vocabulary.VerbFormsView.as_view()),
    path("course/", vocabulary.CourseView.as_view()),
    path("course/<int:number>/", vocabulary.StepView.as_view()),
    path("placement/", vocabulary.PlacementView.as_view()),
    path("course/<int:number>/lessons/", vocabulary.StepLessonsView.as_view()),
    path("course/<int:number>/check/", vocabulary.StepCheckView.as_view()),
    path("srs/today/", srs.TodayView.as_view()),
    path("srs/add/", srs.AddWordView.as_view()),
    path("srs/<int:word_id>/answer/", srs.AnswerView.as_view()),
    path("srs/<int:word_id>/check/", srs.CheckView.as_view()),
    path("trainer/task/", trainer.TaskView.as_view()),
    path("trainer/check/", trainer.CheckView.as_view()),
    path("progress/", progress.ProgressView.as_view()),
    path("progress/reset/", progress.ResetView.as_view()),
    path("progress/week/", progress.WeekView.as_view()),
    path("achievements/", progress.AchievementsView.as_view()),
    path("achievements/seen/", progress.AchievementsSeenView.as_view()),
    path("teacher/groups/", classroom.TeacherGroupsView.as_view()),
    path("teacher/groups/<int:pk>/", classroom.TeacherGroupView.as_view()),
    path("teacher/groups/<int:pk>/code/", classroom.TeacherGroupCodeView.as_view()),
    path("teacher/groups/<int:pk>/students/<int:student_id>/", classroom.TeacherStudentView.as_view()),
    path("groups/", classroom.MyGroupsView.as_view()),
    path("groups/join/", classroom.JoinGroupView.as_view()),
    path("groups/<int:pk>/", classroom.LeaveGroupView.as_view()),
    path("chat/scenarios/", chat.ScenarioListView.as_view()),
    path("chat/conversations/", chat.ConversationListView.as_view()),
    path("chat/conversations/<int:pk>/", chat.ConversationDetailView.as_view()),
    path("chat/conversations/<int:pk>/messages/", chat.SendMessageView.as_view()),
    path("chat/conversations/<int:pk>/messages/stream/", chat.SendMessageStreamView.as_view()),
    path("chat/conversations/<int:pk>/summary/", chat.SummaryView.as_view()),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api)),
    path("healthz", lambda request: JsonResponse({"ok": True})),
]


def spa_index(request):
    """Angular routes (/words, /chat …) all load index.html; the app routes in the browser."""
    index = Path(settings.SPA_DIR) / "index.html"
    if not index.is_file():
        raise Http404
    response = FileResponse(index.open("rb"), content_type="text/html")
    response["Cache-Control"] = "no-cache"
    return response


if settings.SPA_DIR:
    urlpatterns.append(re_path(r"^(?!api/|admin/|static/|healthz).*$", spa_index))

handler404 = "config.exceptions.json_404"
handler500 = "config.exceptions.json_500"
