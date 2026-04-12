import os
import mimetypes
import traceback
from datetime import datetime
from wsgiref.util import FileWrapper

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.http import StreamingHttpResponse
from django.http import JsonResponse
from django.conf import settings

from detection.main import exercise_detection, load_machine_learning_models, EXERCISE_DETECTIONS
from detection.utils import get_static_file_url
import json
from .services import MultiSetSessionManager


@api_view(["GET"])
def stream_video(request):
    """
    Query: video_name
    Stream video get from query
    """
    video_name = request.GET.get("video_name")
    if not video_name:
        return JsonResponse(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": "File name not given",
            },
        )

    static_url = get_static_file_url(f"media/{video_name}")
    if not static_url:
        return JsonResponse(
            status=status.HTTP_404_NOT_FOUND,
            data={
                "message": "File not found",
            },
        )

    # Streamed video as chunked
    video_size = os.path.getsize(static_url)
    content_type, _ = mimetypes.guess_type(static_url)
    content_type = content_type or "application/octet-stream"

    chunk_size = video_size // 10

    response = StreamingHttpResponse(
        FileWrapper(open(static_url, "rb"), chunk_size), content_type=content_type
    )
    response["Content-Length"] = video_size
    response["Accept-Ranges"] = "bytes"
    return response


@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_video(request):
    exercise_type = request.GET.get("type")
    if not exercise_type:
        return JsonResponse(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": "Exercise type has not given",
            },
        )

    # Ensure ML models are loaded (lazy fallback in case app.ready() was skipped)
    load_machine_learning_models()

    try:
        if request.method == "POST":
            if "file" not in request.FILES:
                return JsonResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": "No video file provided"},
                )

            video = request.FILES["file"]

            # Ensure output directories exist
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            os.makedirs(os.path.join(settings.STATICFILES_DIRS[0], "images"), exist_ok=True)

            # Convert any video to .mp4
            now = datetime.now()
            now = int(now.strftime("%Y%m%d%H%M%S"))
            name_to_save = f"video_{now}.mp4"

            # Safely write the uploaded file to disk to avoid InMemoryUploadedFile crashes
            temp_path = os.path.join(settings.MEDIA_ROOT, "temp_" + name_to_save)
            with open(temp_path, 'wb+') as destination:
                for chunk in video.chunks():
                    destination.write(chunk)

            # Process and Save Video
            results, metadata = exercise_detection(
                video_file_path=temp_path,
                video_name_to_save=name_to_save,
                exercise_type=exercise_type,
                rescale_percent=40,
            )
            
            try:
                os.remove(temp_path)
            except Exception:
                pass

            # Convert images' path to URL
            host = request.build_absolute_uri("/")
            for index, error in enumerate(results):
                if error["frame"]:
                    results[index]["frame"] = host + f"static/images/{error['frame']}"

            response_data = {
                "type": exercise_type,
                "processed": True,
                "file_name": name_to_save,
                "details": results,
                "metadata": metadata
            }

            # Handle counter data for backward compatibility
            if exercise_type in ["squat", "lunge", "bicep_curl"]:
                if isinstance(metadata.get("counter"), dict):
                    # For exercise like bicep curl that returns left/right counter
                    response_data["counter"] = metadata["counter"]
                else:
                    response_data["counter"] = metadata.get("counter", 0)

            return JsonResponse(
                status=status.HTTP_200_OK,
                data=response_data,
            )

    except Exception as e:
        print(f"Error Video Processing: {e}")
        traceback.print_exc()

        return JsonResponse(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "error": f"Error: {e}",
            },
        )


@api_view(["POST"])
def start_session(request):
    try:
        body = json.loads(request.body)
        exercise_type = body.get("exercise_type")
        if not exercise_type:
            return JsonResponse({"error": "Missing exercise_type"}, status=400)
            
        from .models import Session
        session = Session.objects.create(exercise_type=exercise_type)
        return JsonResponse({
            'status': 'success',
            'session_id': str(session.session_id)
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def save_session_set(request):
    try:
        body = json.loads(request.body)
        session_id = body.get("session_id")
        exercise_type = body.get("exercise_type")
        set_number = body.get("set_number")
        raw_report = body.get("raw_report")
        
        if not all([session_id, exercise_type, set_number, raw_report]):
            return JsonResponse({"error": "Missing required fields"}, status=400)
            
        result = MultiSetSessionManager.save_set(session_id, exercise_type, set_number, raw_report)
        return JsonResponse(result)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["POST"])
def aggregate_session(request):
    try:
        body = json.loads(request.body)
        session_id = body.get("session_id")
        if not session_id:
            return JsonResponse({"error": "Missing session_id"}, status=400)
            
        result = MultiSetSessionManager.finalize_session(session_id)
        return JsonResponse(result)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
