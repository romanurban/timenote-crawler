import json
import os

# The root directory containing your subfolders
root_dir = 'data'

# Base URL part to be removed and its slashes replaced
base_url = 'https://media2.nekropole.info/'

# Iterate through each subdirectory in the root directory
for subdir in next(os.walk(root_dir))[1]:
    json_file_path = os.path.join(root_dir, subdir, 'data.json')
    new_json_file_path = os.path.join(root_dir, subdir, 'data_clean.json')  # Path for the new, cleaned JSON file
    if os.path.exists(json_file_path):
        # Load the JSON data from the data.json file in the current subdirectory
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Filtered list for entries with existing image files
        filtered_data = []

        for entry in data:
            if 'main_image_url' in entry:
                # Extract the part of the URL after the base URL and replace slashes with underscores
                image_url = entry['main_image_url']
                if image_url.startswith(base_url):
                    file_name = image_url[len(base_url):].replace('/', '_')
                    
                    # Construct the file path assuming the images are stored alongside data.json in the subdirectory
                    file_path = os.path.join(root_dir, subdir, file_name)

                    # Check if the file name exists on the disk
                    if os.path.exists(file_path):
                        # If the file exists, retain the entry
                        filtered_data.append(entry)
                    else:
                        print(f"Image file does NOT exist for entry: {file_name}, entry will be removed.")
                else:
                    print(f"URL does not match base URL pattern for entry: {image_url}, entry will be removed.")
            else:
                print("Entry does not contain a 'main_image_url', and will be removed.")

        # Write the filtered data back to a new JSON file
        with open(new_json_file_path, 'w', encoding='utf-8') as file:
            json.dump(filtered_data, file, indent=4, ensure_ascii=False)

print("Finished processing all subdirectories. Filtered data saved to data_clean.json in each subdirectory.")
