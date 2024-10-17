from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
import logging

import logging

logger = logging.getLogger(__name__)

def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        logger.info(f"Uploading image {image_name} to Minio...")
        client.put_object('images', image_name, file_object, file_object.size)
        return f"http://localhost:9000/images/{image_name}"
    except Exception as e:
        logger.error(f"Error during image upload: {str(e)}")
        return {"error": str(e)}

def add_pic(new_stock, pic):
    logger.info(f"Preparing to upload image for stock id {new_stock.id}")
    client = Minio(           
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    i = new_stock.id
    img_obj_name = f"{i}.png"

    if not pic:
        logger.error("No image file provided")
        return Response({"error": "Нет файла для изображения логотипа."})
    
    result = process_file_upload(pic, client, img_obj_name)

    if 'error' in result:
        logger.error(f"Image upload failed: {result['error']}")
        return Response(result)

    new_stock.url = result
    new_stock.save()

    logger.info(f"Image uploaded successfully for stock id {new_stock.id}")
    return Response({"message": "success"})