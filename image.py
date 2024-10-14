import os
import json
import shutil
from PIL import Image
import piexif
from datetime import datetime
import pillow_heif

# Configuration
SOURCE_DIR = "D:/Google Photos"  # Replace with your source directory path
OUTPUT_DIR = "C:/Googlephotos"  # Output directory
NOT_FOUND_DIR = os.path.join(OUTPUT_DIR, "Not_Found")  # Directory for not found images/videos
VIDEO_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "Videos")  # Directory for videos

# Supported image and video extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.HEIC', '.HEIF', '.JPG', '.JPEG','PNG', }
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.MOV', '.MP4'}  # Add more video formats as needed

def get_exif_datetime(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y:%m:%d %H:%M:%S"), dt.year  # Returning year for folder structuring
    except ValueError:
        return None, None

def get_photo_taken_time(metadata):
    """Extracts the photo taken time from metadata and returns formatted datetime and year."""
    try:
        if 'photoTakenTime' in metadata:
            timestamp = metadata['photoTakenTime']['timestamp']
            dt = datetime.utcfromtimestamp(int(timestamp))
            return dt.strftime("%Y:%m:%d %H:%M:%S"), dt.year  # Returning year for folder structuring
    except Exception as e:
        print(f"Error extracting photo taken time: {e}")
    return None, None

def get_gps_info(metadata):
    """Extracts GPS information from metadata."""
    gps_info = {}
    try:
        if 'geoData' in metadata:
            geo = metadata['geoData']
            if 'latitude' in geo and 'longitude' in geo:
                lat = geo['latitude']
                lon = geo['longitude']

                def decimal_to_dms(deg):
                    d = int(deg)
                    min_float = (deg - d) * 60
                    m = int(min_float)
                    sec = round((min_float - m) * 60 * 100)
                    return ((d, 1), (m, 1), (sec, 100))

                lat_dms = decimal_to_dms(abs(lat))
                lon_dms = decimal_to_dms(abs(lon))

                gps_info[piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
                gps_info[piexif.GPSIFD.GPSLatitude] = lat_dms
                gps_info[piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'
                gps_info[piexif.GPSIFD.GPSLongitude] = lon_dms
    except Exception as e:
        print(f"Error extracting GPS info: {e}")
    return gps_info

def embed_metadata(image_path, json_path, output_image_path):
    """Embed metadata from JSON into the image and save to output_path."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            print(f"Metadata loaded for {image_path}")

        if image_path.lower().endswith(('.heic', '.heif')):
            img = pillow_heif.read_heif(image_path)
            img = Image.frombytes(img.mode, img.size, img.data)
        else:
            img = Image.open(image_path)

        img = img.convert("RGB")
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Embed DateTimeOriginal from photoTakenTime
        dt_str, year = get_photo_taken_time(metadata)
        if dt_str:
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = dt_str.encode('utf-8')

        # Embed GPS Info
        gps_info = get_gps_info(metadata)
        if gps_info:
            exif_dict['GPS'] = gps_info

        # Embed Description (as ImageDescription)
        if 'description' in metadata:
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = metadata['description'].encode('utf-8')

        exif_bytes = piexif.dump(exif_dict)

        # Save the new image with embedded EXIF
        img.save(output_image_path, "jpeg", exif=exif_bytes)
        print(f"Metadata embedded and saved to: {output_image_path}")

    except Exception as e:
        print(f"Failed to embed metadata for {image_path}: {e}")

def find_image_file(image_title, source_dir):
    """Search for the corresponding image file based on the title in the JSON metadata."""
    title_without_ext, _ = os.path.splitext(image_title)  # Get title without extension
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower() == image_title.lower():
                return os.path.join(root, file)
    return None

def process_image(image_title, json_path, output_image_path):
    """Process the image based on the JSON metadata and handle missing files."""
    # If JSON metadata exists, embed metadata
    if json_path and os.path.exists(json_path):
        # Find the corresponding image file
        image_path = find_image_file(image_title, SOURCE_DIR)
        if image_path:
            embed_metadata(image_path, json_path, output_image_path)
        else:
            print(f"Image not found for {image_title}, copying JSON to Not Found folder.")
            if not os.path.exists(NOT_FOUND_DIR):
                os.makedirs(NOT_FOUND_DIR)
            shutil.copy(json_path, os.path.join(NOT_FOUND_DIR, os.path.basename(json_path)))
    else:
        print(f"No metadata found for {image_title}, copying JSON to Not Found folder.")
        if not os.path.exists(NOT_FOUND_DIR):
            os.makedirs(NOT_FOUND_DIR)
        shutil.copy(json_path, os.path.join(NOT_FOUND_DIR, os.path.basename(json_path)))

def process_video(video_title, json_path):
    """Process the video file and copy it to the designated output directory."""
    video_path = find_image_file(video_title, SOURCE_DIR)  # Reuse find_image_file to locate videos
    if video_path:
        print(f"Video found: {video_path}. Copying to {VIDEO_OUTPUT_DIR}.")
        shutil.copy(video_path, VIDEO_OUTPUT_DIR)
    else:
        print(f"Video not found for {video_title}, copying JSON to Not Found folder.")
        if not os.path.exists(NOT_FOUND_DIR):
            os.makedirs(NOT_FOUND_DIR)
        shutil.copy(json_path, os.path.join(NOT_FOUND_DIR, os.path.basename(json_path)))

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(NOT_FOUND_DIR, exist_ok=True)  # Create Not Found directory
    os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)  # Create Videos directory

    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(SOURCE_DIR):
        for filename in files:
            if filename.lower().endswith('.json'):
                json_path = os.path.join(root, filename)

                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        title = metadata['title']  # Extract the image/video title

                    # Determine if the title corresponds to an image or a video
                    _, ext = os.path.splitext(title.lower())
                    if ext in IMAGE_EXTENSIONS:
                        dt_str, year = get_photo_taken_time(metadata)

                        # Ensure the output is categorized by year
                        year_folder = os.path.join(OUTPUT_DIR, str(year))
                        os.makedirs(year_folder, exist_ok=True)

                        # Output path for the processed image
                        output_image_path = os.path.join(year_folder, title)

                        # Process the image based on the metadata
                        process_image(title, json_path, output_image_path)

                    elif ext in VIDEO_EXTENSIONS:
                        # Process the video file
                        process_video(title, json_path)
                    else:
                        print(f"Unsupported file type for {title}")

                except Exception as e:
                    print(f"Error processing JSON file {filename}: {e}")

if __name__ == "__main__":
    print(f"Starting the script with SOURCE_DIR: {SOURCE_DIR}")
    if os.path.exists(SOURCE_DIR):
        main()
    else:
        print(f"Source directory {SOURCE_DIR} does not exist!")
