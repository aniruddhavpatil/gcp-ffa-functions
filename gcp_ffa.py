
import os
import tempfile
from werkzeug.utils import secure_filename
from google.cloud import storage
import json


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "gcp-ffa-images"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )
    return blob.public_url



def cors_enabled_function(request):
    # For more information about CORS and CORS preflight requests, see
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request
    # for more information.

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    blob_url = parse_multipart(request)
    objects = localize_objects_uri(blob_url)


    return (json.dumps(objects), 200, headers)


# Helper function that computes the filepath to save files to
def get_file_path(filename):
    # Note: tempfile.gettempdir() points to an in-memory file system
    # on GCF. Thus, any files in it must fit in the instance's memory.
    file_name = secure_filename(filename)
    return os.path.join(tempfile.gettempdir(), file_name)


def parse_multipart(request):
    """ Parses a 'multipart/form-data' upload request
    Args:
        request (flask.Request): The request object.
    Returns:
        The response text, or any set of values that can be turned into a
         Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """

    # This code will process each non-file field in the form
    fields = {}
    data = request.form.to_dict()
    for field in data:
        fields[field] = data[field]
        print('Processed field: %s' % field)

    # This code will process each file uploaded
    blob_urls = None
    files = request.files.to_dict()
    for file_name, file in files.items():
        # Note: GCF may not keep files saved locally between invocations.
        # If you want to preserve the uploaded files, you should save them
        # to another location (such as a Cloud Storage bucket).
        file_path = get_file_path(file_name)
        file.save(file_path)
        print('FILE PATH',file_path)
        blob_url = upload_blob("gcp-ffa-images", file_path, file_name)
        print('Processed file: %s' % file_name)

    # Clear temporary directory
    for file_name in files:
        file_path = get_file_path(file_name)
        os.remove(file_path)

    # # Set CORS headers for the preflight request
    # if request.method == 'OPTIONS':
    #     # Allows GET requests from any origin with the Content-Type
    #     # header and caches preflight response for an 3600s
    #     headers = {
    #         'Access-Control-Allow-Origin': '*',
    #         'Access-Control-Allow-Methods': 'GET',
    #         'Access-Control-Allow-Headers': 'Content-Type',
    #         'Access-Control-Max-Age': '3600'
    #     }

    #     return ('', 204, headers)

    # # Set CORS headers for the main request
    # headers = {
    #     'Access-Control-Allow-Origin': '*'
    # }

    return blob_url


def localize_objects_uri(uri):
    """Localize objects in the image on Google Cloud Storage

    Args:
    uri: The path to the file in Google Cloud Storage (gs://...)
    """
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    image = vision.Image()
    image.source.image_uri = uri

    objects = client.object_localization(
        image=image).localized_object_annotations

    print('Number of objects found: {}'.format(len(objects)))
    object_list = []
    for object_ in objects:
        list_item = {
            'confidence': object_.score,
            'name': object_.name,
            'vertices': []
        }

        print('\n{} (confidence: {})'.format(object_.name, object_.score))
        print('Normalized bounding polygon vertices: ')
        for vertex in object_.bounding_poly.normalized_vertices:
            print(' - ({}, {})'.format(vertex.x, vertex.y))
            list_item['vertices'].append((vertex.x, vertex.y))
        object_list.append(list_item)
    return object_list