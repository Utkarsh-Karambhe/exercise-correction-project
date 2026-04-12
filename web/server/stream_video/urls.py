from django.urls import path
from . import views

urlpatterns = [
    path("stream", views.stream_video, name="stream"),
    path("upload", views.upload_video, name="upload"),
    path("session/start", views.start_session, name="start_session"),
    path("session/set/save", views.save_session_set, name="save_session_set"),
    path("session/aggregate", views.aggregate_session, name="aggregate_session"),
]
