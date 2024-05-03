import os
import json
import threading
from random import randint
import requests
import time
from urllib.parse import urlparse

def download_image(image_url, save_path):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=128):
                    f.write(chunk)
            print(f"Successfully downloaded {save_path}")
    except Exception as e:
        print(f"Failed to download {image_url}. Error: {e}")

def process_json_file(json_path, base_url):
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    for index, item in enumerate(data, start=1):
        image_url = item.get('main_image_url')
        if image_url and image_url.startswith(base_url):
            filename = image_url.replace(base_url, '').replace('/', '_')
            save_path = os.path.join(os.path.dirname(json_path), filename)
            
            if not os.path.exists(save_path):
                print(f"Downloading {index}/{len(data)}: {filename}")
                download_image(image_url, save_path)
                # polite pause after each download
                time.sleep(randint(1, 3))

def find_and_process_json_files(start_directory, base_url):
    json_files = []
    for root, dirs, files in os.walk(start_directory):
        for file in files:
            if file == 'data.json':
                json_files.append(os.path.join(root, file))

    for json_path in json_files:
        threading.Thread(target=process_json_file, args=(json_path, base_url)).start()

base_url = 'https://media2.nekropole.info/'
start_directory = 'data/'
find_and_process_json_files(start_directory, base_url)
