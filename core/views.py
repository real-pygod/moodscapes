# myapp/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import UploadedImage
from .serializers import UploadedImageSerializer
import requests
import logging
import os
import traceback

logger = logging.getLogger(__name__)

class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        print("HERE IN THE UPLOADED IMAGE METHOD")
        serializer = UploadedImageSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            image_url = request.build_absolute_uri(instance.image.url)

            logger.debug(f'Image URL: {image_url}')

            # Call 3D conversion API
            headers = {
                "Authorization": f"Bearer {settings.MESHY_API_KEY}"
            }
            payload = {
                "image_url": image_url,
                "enable_pbr": True,
            }

            logger.debug(f'Payload: {payload}')
            print(f'Payload: {payload}')

            try:
                response = requests.post("https://api.meshy.ai/v1/image-to-3d", headers=headers, json=payload)
                response.raise_for_status()
                task_id = response.json()["result"]

                # Save the task ID and initial status
                instance.task_id = task_id
                instance.status = 'processing'
                instance.save()

                # Provide the task ID to the client
                return Response({'task_id': task_id, 'status': 'processing', "model_urls":[]}, status=202)

            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 429:
                    logger.error('Too Many Requests: Rate limit exceeded.')
                    print('Too Many Requests: Rate limit exceeded.')
                    return Response({'error': 'Rate limit exceeded. Please try again later.'}, status=429)
                else:
                    logger.error(f'HTTP error occurred: {http_err}')
                    print(f'HTTP error occurred: {http_err}')
                    return Response({'error': 'Failed to process the image.'}, status=response.status_code)
            except Exception as err:
                logger.error(f'Other error occurred: {err}')
                print(f'Other error occurred: {err}')
                return Response({'error': 'An unexpected error occurred.'}, status=500)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=400)

class ImageStatusView(APIView):
    def get(self, request, task_id, *args, **kwargs):
        print("GET REQUEST IS HERE!!!")
        print(task_id)
        try:
            image = UploadedImage.objects.get(task_id=task_id)
        except UploadedImage.DoesNotExist:
            print("NOT FOUND")
            return Response({'error': 'Task ID not found'}, status=404)

        if image.status == "processing" or image.status == "completed":
        # if image.status == 'processing':
            headers = {
                "Authorization": f"Bearer {settings.MESHY_API_KEY}"
            }

            try:
                response = requests.get(f"https://api.meshy.ai/v1/image-to-3d/{task_id}", headers=headers)
                response.raise_for_status()
                model_data = response.json()
                image.model_data = model_data
                image.status = "completed"
                image.save()

                # Download model files and save them locally
                model_urls = model_data.get("model_urls", {})
                downloaded_files = {}

                for key, url in model_urls.items():
                    try:
                        file_response = requests.get(url)
                        if file_response.status_code == 200:
                            file_extension = url.split('.')[-1].split('?')[0]
                            file_name = f"{task_id}_{key}.{file_extension}"
                            if len(file_name) > 100:  # Ensure filename length is acceptable
                                file_name = f"{task_id}_{key}.{file_extension}"
                            file_path = default_storage.save(file_name, ContentFile(file_response.content))
                            downloaded_files[key] = request.build_absolute_uri(default_storage.url(file_path))
                    except Exception as e:
                        logger.error(f"Error downloading file {key} from {url}: {e}")
                        continue

                # Update model_data with local URLs
                model_data["model_urls"] = downloaded_files
                image.model_data = model_data
                image.save()

                return Response({'status': 'completed', 'model_urls': downloaded_files, "task_id": task_id}, status=200)

            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 429:
                    logger.error('Too Many Requests: Rate limit exceeded.')
                    print('Too Many Requests: Rate limit exceeded.')
                    return Response({'error': 'Rate limit exceeded. Please try again later.'}, status=429)
                elif response.status_code == 404:
                    logger.error('Task not yet complete.')
                    print('Task not yet complete.')
                    return Response({'status': 'processing'}, status=202)
                else:
                    logger.error(f'HTTP error occurred: {http_err}')
                    print(f'HTTP error occurred: {http_err}')
                    return Response({'error': 'Failed to retrieve the model data.'}, status=response.status_code)
            except Exception as err:
                traceback.print_exc()
                logger.error(f'Other error occurred: {err}')
                print(f'Other error occurred: {err}')
                return Response({'error': 'An unexpected error occurred.'}, status=500)
        else:
            print(image.__dict__)
            return Response({'status': image.status, 'model_urls': image.model_data.get("model_urls", {}), "task_id": image.task_id})
