import requests
from bs4 import BeautifulSoup
import time
import random
import pprint
import json
import os
import re

# base URL for the cemetery person list
BASE_URL = "https://timenote.info/en/person/list"

# cemetery IDs for which we want to crawl the data
cemeteries = [147]

# request params
params = {
    'cemetery_id': None, # set for each cemetery
    'order': 4, # order by date of death
    'start': 0 # pagination
}

# resulting structure
data = {
    # cemetery_id: [list of data entries for each person]
}

def get_cemetery_name(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.find('title').get_text()
    # remove any characters not suitable for directory names
    valid_name = re.sub('[^a-zA-Z0-9 \n\.]', '', title)
    return valid_name.strip()

def get_individual_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # check whether the main image is missing
    no_image = soup.select_one('.photo-main .no_person_image')
    if no_image:
        # skip person if no main image
        return None
    
    person_name_container = soup.find('span', class_='person-name')
    if person_name_container:
        # extract the text
        person_name = ''.join(person_name_container.find_all(text=True, recursive=False)).strip()
    else:
        person_name = "Name not found"

    # get the first image URL
    main_image_a_tag = soup.select_one('.person-header-images .photo-main a')
    if main_image_a_tag and 'href' in main_image_a_tag.attrs:
        main_image_url = 'https:' + main_image_a_tag['href']
    else:
        # no image found
        return None

    # looking for additional details
    attributes = {dt.get_text(strip=True): dd.get_text(strip=True) for dt, dd in zip(soup.select('.attributes dt'), soup.select('.attributes dd'))}

    birth_date = attributes.get('Birth Date:', None)
    death_date = attributes.get('Death date:', None)
    nationality = attributes.get('Nationality:', None)
    maiden_name = attributes.get('Person\'s maiden name:', None)
    extra_names = attributes.get('Extra names:', None)
    patronymic = attributes.get('Patronymic:', None)
    cemetery_info = attributes.get('Cemetery:', None)

    return {
        'main_image_url': main_image_url,
        'person_name': person_name,
        'birth_date': birth_date,
        'death_date': death_date,
        'maiden_name': maiden_name,
        'extra_names': extra_names,
        'patronymic': patronymic,
        'nationality': nationality,
        'cemetery_info': cemetery_info
    }

def get_total_records(cemetery_id):
    params['cemetery_id'] = cemetery_id
    params['start'] = 0
    response = requests.get(BASE_URL, params=params)
    soup = BeautifulSoup(response.content, 'html.parser')
    pagination_links = soup.select('.splits a')
    if not pagination_links:
        return 0  # no pagination links found
    last_page_link = pagination_links[-1]['href']
    last_page_start = int(last_page_link.split('start=')[-1])
    last_page_text = pagination_links[-1].text
    records_on_last_page = int(last_page_text.split('-')[-1]) - last_page_start
    total_records = last_page_start + records_on_last_page
    return total_records

def save_data_to_disk(cemetery_name, cemetery_data):
    # sanitize the cemetery name to use it as a directory name
    directory_name = re.sub('[^a-zA-Z0-9 \n\.]', '', cemetery_name).replace(' ', '_')
    save_directory = f'data/{directory_name}'
    
    os.makedirs(save_directory, exist_ok=True)
    
    json_file_path = os.path.join(save_directory, 'data.json')
    
    # save results to JSON
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(cemetery_data, json_file, ensure_ascii=False, indent=4)
    
    print(f'Data for cemetery {cemetery_name} has been saved to {json_file_path}')

def crawl_cemetery(cemetery_id):
    current_start = 0
    cemetery_data = []
    params['cemetery_id'] = cemetery_id
    cemetery_url = "https://timenote.info/en/cemetery/view?id=" + str(cemetery_id)
    cemetery_name = get_cemetery_name(cemetery_url)
    total_records = get_total_records(cemetery_id)

    print(f"Crawling cemetery: {cemetery_name}, id: {cemetery_id}, total records: {total_records}")

    while True:
        params['start'] = current_start
        print(f"Crawling next 20 records {current_start}/{total_records} for cemetery id: {cemetery_id}")
        response = requests.get(BASE_URL, params=params)
        soup = BeautifulSoup(response.content, 'html.parser')
    

        rows = soup.select('table tbody tr')
        if not rows:
            break

        for row in rows:
            try:
                href = row.select_one('.person-link')['href']  # Define href before checking for images
                no_image_male = row.select_one('.no-image-male')
                no_image_female = row.select_one('.no-image-female')
                if no_image_male or no_image_female:
                    print(f"Skipping {href} because no image found")
                    continue

                detailed_data = get_individual_data(f"https://timenote.info{href}")
                
                if detailed_data is not None: 
                    cleaned_data = {k: v for k, v in detailed_data.items() if v is not None}

                    pp = pprint.PrettyPrinter(indent=4)
                    pp.pprint(cleaned_data)

                    cemetery_data.append(cleaned_data)
                
                # random sleep duration to be polite and not overload the server
                time.sleep(random.uniform(0.5, 2.5))
            except Exception as e:
                print(f"An error occurred processing {href}: {e}")
                continue

        # next page link
        next_page_link = soup.select_one('a[rel="next"]')
        if next_page_link and 'href' in next_page_link.attrs:
            next_page_url = next_page_link['href']
            next_start = next_page_url.split('start=')[-1]
            current_start = int(next_start)
        else:
            break

    data[cemetery_id] = cemetery_data
    save_data_to_disk(cemetery_name, cemetery_data)

for cemetery_id in cemeteries:
    crawl_cemetery(cemetery_id)