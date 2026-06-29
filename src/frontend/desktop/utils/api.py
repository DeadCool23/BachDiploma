import requests
import os

def call_reduce_api(api_url, images_list):
    files = []
    for img_path in images_list:
        files.append(('images', (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg')))
    
    response = requests.post(f"{api_url}/api/v1/images/reduce/", files=files)
    
    for _, (_, file_obj, _) in files:
        file_obj.close()
    
    return response

def call_scale_api(api_url, image_path, scale, method):
    if method == "dev_method":
        endpoint = "/api/v1/image/scale/method/"
        params = {"scale": scale}
    else:
        endpoint = "/api/v1/image/scale/interpolation/"
        params = {"scale": scale, "interpolation": method}
    
    with open(image_path, 'rb') as f:
        files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
        response = requests.post(f"{api_url}{endpoint}", params=params, files=files)
    
    return response

def get_filename_from_response(response, scale, method, original_path):
    content_disposition = response.headers.get('Content-Disposition')
    if content_disposition and 'filename=' in content_disposition:
        import re
        filename_match = re.search(r'filename[^;=\n]*=(["\'])(.*?)\1', content_disposition)
        if filename_match:
            return filename_match.group(2)
        filename_match = re.search(r'filename=([^;]+)', content_disposition)
        if filename_match:
            return filename_match.group(1).strip('"\'')
    return f"scaled_image_{int(scale)}x_{method}.jpg"