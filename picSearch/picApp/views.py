# Views for picApp
# Provides home, submit_child, and search_child views.
import os
# Set DEEPFACE_HOME to project root (two levels up) for DeepFace model storage
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ.setdefault('DEEPFACE_HOME', project_root)
# Ensure the .deepface/weights directory exists
os.makedirs(os.path.join(project_root, '.deepface', 'weights'), exist_ok=True)

import tempfile
import numpy as np
import cv2
from django.conf import settings
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.contrib import messages
from deepface import DeepFace
from .models import MissingChild
from .forms import MissingChildForm

def get_facenet_model():
    """Lazily load and cache the Facenet model."""
    if not hasattr(get_facenet_model, "model"):
        # Model will be stored in the .deepface/weights directory set at module import.
        get_facenet_model.model = DeepFace.build_model("Facenet")
    return get_facenet_model.model
get_facenet_model()  # Preload model at import time for faster first submission



def home(request):
    """Render a simple home page."""
    return render(request, "home.html")


def submit_child(request):
    if request.method == "POST":
        form = MissingChildForm(request.POST, request.FILES)
        if form.is_valid():
            child = form.save(commit=False)
            image_name = request.FILES["image"].name
            image_path = os.path.join("missing_children", image_name)
            image_full_path = os.path.join(settings.MEDIA_ROOT, image_path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(image_full_path), exist_ok=True)

            # Save image
            default_storage.save(image_path, request.FILES["image"])
            child.image.name = image_path
            child.image._committed = True

            # Generate encoding using preloaded model to avoid repeated download
            encoding = DeepFace.represent(img_path=image_full_path, model_name='Facenet', enforce_detection=False)
            child.image_encoding = np.array(encoding).tobytes()
            child.save()
            messages.success(request, 'Missing child submitted successfully!')
            return redirect('search_child')
    else:
        form = MissingChildForm()
    return render(request, "submit_child.html", {"form": form})


def search_child(request):
    if request.method == "POST":
        uploaded = request.FILES["image"]
        image_data = uploaded.read()

        # Convert uploaded image to base64 Data URL for front-end query display and comparison
        import base64
        search_image_b64 = base64.b64encode(image_data).decode('utf-8')
        search_image_url = f"data:{uploaded.content_type};base64,{search_image_b64}"

        # Write to a temporary file
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(image_data)
        temp.flush()
        try:
            # Verify faces exist
            DeepFace.extract_faces(temp.name, enforce_detection=True)
        except ValueError:
            temp.close()
            os.unlink(temp.name)
            return render(request, "search_child.html", {"error": "No face detected. Please upload an image with a face."})

        similar = []
        for child in MissingChild.objects.all():
            child_path = os.path.join(settings.MEDIA_ROOT, child.image.name)
            result = DeepFace.verify(temp.name, child_path, model_name="Facenet", distance_metric="euclidean_l2", enforce_detection=False)
            if result["verified"]:
                distance = float(result["distance"])
                similarity = round(1 / (1 + distance) * 100, 2)
                if similarity > 60:
                    similar.append((child, similarity))
        # Clean up temp file
        temp.close()
        os.unlink(temp.name)
        similar.sort(key=lambda x: x[1], reverse=True)
        return render(request, "search_results.html", {
            "similar_children": similar,
            "search_image_url": search_image_url
        })
    return render(request, "search_child.html")
