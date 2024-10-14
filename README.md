# Photo-Metadata
A Simple Script to Embed the Metadata into your Google Takeout Photos 

# How It Works
- The script looks for JSON metadata files in the specified folder.
- For each JSON file, it identifies the corresponding image file (the one that has the same base name).
- It reads the metadata from the JSON file and overlays it onto the image.
- The new image, with metadata overlaid, is saved to a separate folder.

# Usage
- Set the folder paths: Update the the `SOURCE_DIR` and `OUTPUT_DIR`
- install the requirements
- Run image.py : `python image.py`
- The script will process each folder recursively, find the corresponding images for each JSON file, overlay the metadata, and save the new images in the specified output folder.
