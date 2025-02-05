import os
import re
import argparse
import json
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import sys
from collections import OrderedDict

def is_json(data):
    """
    Check if the given data is in JSON format.
    """
    try:
        json.loads(data)
        return True
    except (ValueError, TypeError):
        return False

def extract_image_metadata(image_path):
    """
    Extract metadata from an image file (PNG or JPG).
    Returns a dictionary of metadata or None if no metadata is found.
    """
    try:
        with Image.open(image_path) as img:
            metadata = {}
            
            # Extract basic metadata (common to both PNG and JPG)
            if hasattr(img, 'info'):
                metadata.update(img.info)
            
            # Extract EXIF metadata (specific to JPG)
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        metadata[tag_name] = value
            
            if not metadata:
                return None
            return metadata
    except Exception as e:
        print(f"Warning: Could not read metadata from {image_path}: {e}")
        return None

def merge_json_data(existing_json, new_json):
    """
    Merge two JSON objects. The existing JSON data is placed at the top.
    """
    merged = OrderedDict()
    
    # Ensure 'post_training_processing' is at the top
    if "post_training_processing" in existing_json:
        merged["post_training_processing"] = existing_json["post_training_processing"]
    elif "post_training_processing" in new_json:
        merged["post_training_processing"] = new_json["post_training_processing"]
    
    # Merge the rest of the data (existing data takes precedence)
    for key, value in existing_json.items():
        if key != "post_training_processing":
            merged[key] = value
    for key, value in new_json.items():
        if key != "post_training_processing" and key not in merged:
            merged[key] = value
    
    return merged

def fix_floating_point_filenames(filename):
    """
    Fix floating-point numbers in filenames to always have two digits after the decimal point.
    Example: '1.0' -> '1.00', '2.1' -> '2.10'.
    """
    # Use regex to find floating-point numbers in the filename
    parts = re.split(r'(\d+\.\d+)', filename)
    for i, part in enumerate(parts):
        if re.match(r'\d+\.\d+', part):
            # Format the floating-point number to two decimal places
            parts[i] = f"{float(part):.2f}"
    return ''.join(parts)

def rename_file(image_path, new_filename, dry_run=False):
    """
    Rename the image file to the new filename.
    If dry_run is True, only print a message and do not rename the file.
    """
    new_path = image_path.with_name(new_filename)

    # Check if the new filename is the same as the old filename
    if image_path.name == new_filename:
        # No change, nothing to do
        return
    
    if dry_run:
        print(f"Dry run: Would rename {image_path} to {new_path}")
    else:
        try:
            os.rename(image_path, new_path)
            print(f"Renamed {image_path} to {new_path}")
        except Exception as e:
            print(f"Error: Could not rename {image_path} to {new_filename}: {e}")

def write_metadata(image_path, metadata, dry_run=False, fix_filenames=False, command=None, force_json=False):
    """
    Write metadata to a file. If the metadata is JSON, overwrite the existing .json file
    with the merged data. Otherwise, save it as a .txt file.
    If dry_run is True, only print a message and do not modify any files.
    If fix_filenames is True, fix floating-point numbers in filenames and rename the image file.
    """
    # Check for an existing .json file with the same name (before fixing filenames)
    existing_json_path = image_path.with_suffix('.json')
    existing_json = None
    if existing_json_path.exists():
        new_filename = fix_floating_point_filenames(existing_json_path.stem) + existing_json_path.suffix
        rename_file(existing_json_path, new_filename, dry_run)
        if not dry_run:
            existing_json_path = existing_json_path.with_name(new_filename)  # Update existing_json_path to the new filename
        with open(existing_json_path, 'r') as existing_file:
            existing_json = json.load(existing_file, object_pairs_hook=OrderedDict)
            print(f"Found existing JSON metadata in: {existing_json_path}")
    
    # Fix filenames if requested
    if fix_filenames:
        new_filename = fix_floating_point_filenames(image_path.stem) + image_path.suffix
        rename_file(image_path, new_filename, dry_run)
        if not dry_run:
            image_path = image_path.with_name(new_filename)  # Update image_path to the new filename

    # Check if metadata is JSON-formatted
    json_metadata = None
    for key, value in metadata.items():
        if isinstance(value, str) and is_json(value):
            json_metadata = value
            break
    
    if json_metadata:
        # Parse JSON metadata from the image
        try:
            parsed_json = json.loads(json_metadata, object_pairs_hook=OrderedDict)
            
            # Add post_training_processing array with the command used to run the script
            if "post_training_processing" not in parsed_json:
                parsed_json["post_training_processing"] = []
            
            # Check if the script's command is already in the post_training_processing array
            if command in parsed_json["post_training_processing"] and not force_json:
                print(f"File {image_path} has already been processed by this script. Use --force-json to overwrite.")
                return
            
            parsed_json["post_training_processing"].append(command)
            
            # Merge JSON data with existing JSON (if any)
            if existing_json:
                merged_json = merge_json_data(existing_json, parsed_json)
            else:
                merged_json = parsed_json
            
            formatted_json = json.dumps(merged_json, indent=4)  # 4 spaces for indentation
            
            if dry_run:
                print(f"Dry run: Would overwrite {existing_json_path} with merged JSON data.")
            else:
                # Overwrite the existing .json file
                with open(existing_json_path, 'w') as json_file:
                    json_file.write(formatted_json)
                print(f"Overwrote JSON metadata in: {existing_json_path}")
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON metadata in {image_path}: {e}")
            # Fallback to saving as .txt
            txt_path = image_path.with_suffix('.txt')
            
            if dry_run:
                print(f"Dry run: Would save metadata to: {txt_path}")
            else:
                with open(txt_path, 'w') as txt_file:
                    for key, value in metadata.items():
                        txt_file.write(f"{key}: {value}\n")
                print(f"Saved metadata to: {txt_path}")
    else:
        # Save as .txt
        txt_path = image_path.with_suffix('.txt')
        
        if dry_run:
            print(f"Dry run: Would save metadata to: {txt_path}")
        else:
            with open(txt_path, 'w') as txt_file:
                for key, value in metadata.items():
                    txt_file.write(f"{key}: {value}\n")
            print(f"Saved metadata to: {txt_path}")

def clean_orphaned_files(directory, recursive=False, dry_run=False):
    """
    Delete orphaned .json and .txt files that don't have a corresponding image file.
    If dry_run is True, only print a message and do not delete any files.
    """
    if recursive:
        # Traverse recursively
        for root, dirs, files in os.walk(directory, topdown=False):
            # Clean orphaned files
            for file in files:
                if file.lower().endswith(('.json', '.txt')):
                    file_path = Path(root) / file
                    image_path = file_path.with_suffix('.png')
                    if not image_path.exists():
                        image_path = file_path.with_suffix('.jpg')
                        if not image_path.exists():
                            image_path = file_path.with_suffix('.jpeg')
                            if not image_path.exists():
                                if dry_run:
                                    print(f"Dry run: Would delete orphaned file {file_path}")
                                else:
                                    try:
                                        os.remove(file_path)
                                        print(f"Deleted orphaned file: {file_path}")
                                    except Exception as e:
                                        print(f"Error: Could not delete {file_path}: {e}")
            
            # Clean empty directories
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not os.listdir(dir_path):  # Check if directory is empty
                        if dry_run:
                            print(f"Dry run: Would delete empty directory {dir_path}")
                        else:
                            os.rmdir(dir_path)
                            print(f"Deleted empty directory: {dir_path}")
                except Exception as e:
                    print(f"Error: Could not delete directory {dir_path}: {e}")
    else:
        # Traverse only the top-level directory
        for file in os.listdir(directory):
            if file.lower().endswith(('.json', '.txt')):
                file_path = Path(directory) / file
                image_path = file_path.with_suffix('.png')
                if not image_path.exists():
                    image_path = file_path.with_suffix('.jpg')
                    if not image_path.exists():
                        image_path = file_path.with_suffix('.jpeg')
                        if not image_path.exists():
                            if dry_run:
                                print(f"Dry run: Would delete orphaned file {file_path}")
                            else:
                                try:
                                    os.remove(file_path)
                                    print(f"Deleted orphaned file: {file_path}")
                                except Exception as e:
                                    print(f"Error: Could not delete {file_path}: {e}")

def process_image_files(directory, recursive=False, dry_run=False, fix_filenames=False, command=None, force_json=False):
    """
    Traverse the directory (recursively if specified), process image files, and extract metadata.
    """
    if recursive:
        # Traverse recursively
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = Path(root) / file
                    metadata = extract_image_metadata(image_path)
                    
                    if metadata:
                        print(f"Extracting metadata from: {image_path}")
                        write_metadata(image_path, metadata, dry_run, fix_filenames, command, force_json)
                    else:
                        print(f"Warning: No metadata found in {image_path}")
    else:
        # Traverse only the top-level directory
        for file in os.listdir(directory):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = Path(directory) / file
                metadata = extract_image_metadata(image_path)
                
                if metadata:
                    print(f"Extracting metadata from: {image_path}")
                    write_metadata(image_path, metadata, dry_run, fix_filenames, command, force_json)
                else:
                    print(f"Warning: No metadata found in {image_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract metadata from image files (PNG/JPG) and save to .txt or .json files. Merge with existing .json files if present.",
        epilog="Examples:\n"
               "  export_metadata_json.py /path/to/directory\n"
               "  export_metadata_json.py /path/to/directory -r\n"
               "  export_metadata_json.py /path/to/directory -n\n"
               "  export_metadata_json.py /path/to/directory -r -n\n"
               "  export_metadata_json.py /path/to/directory -f\n"
               "  export_metadata_json.py /path/to/directory -r -f",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'directory',
        type=str,
        help="The directory to traverse."
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help="Traverse directories recursively."
    )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help="Simulate the process without modifying files."
    )
    parser.add_argument(
        '-f', '--fix-filenames',
        action='store_true',
        help="Fix floating-point numbers in filenames to have two digits after the decimal point."
    )
    parser.add_argument(
        '--force-json',
        action='store_true',
        help="Force overwrite of JSON files even if they have already been processed by this script."
    )
    parser.add_argument(
        '-c', '--clean',
        action='store_true',
        help="Delete orphaned .json and .txt files and empty directories."
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory.")
        return
    
    # Construct the full command used to run the script
    command = " ".join(sys.argv)
    
    process_image_files(args.directory, args.recursive, args.dry_run, args.fix_filenames, command, args.force_json)
    if args.clean:
        clean_orphaned_files(args.directory, args.recursive, args.dry_run)

if __name__ == "__main__":
    main()