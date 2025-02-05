# Export Metadata to JSON (`export_meta_data_json.py`)

This Python script extracts metadata from image files (PNG and JPG) and saves it to `.txt` or `.json` files. It can also merge metadata with existing `.json` files, fix floating-point numbers in filenames, and clean up orphaned metadata files.

---

## Features

- **Extract Metadata**: Extracts metadata from PNG and JPG images, including EXIF data for JPG files.
- **Save Metadata**: Saves metadata to `.txt` or `.json` files. If a `.json` file already exists, the script merges the new metadata with the existing data.
- **Fix Filenames**: Fixes floating-point numbers in filenames to ensure they have two digits after the decimal point (e.g., `1.0` becomes `1.00`).
- **Dry Run**: Simulates the process without modifying any files.
- **Clean Orphaned Files**: Deletes orphaned `.json` and `.txt` files that do not have a corresponding image file.
- **Recursive Processing**: Processes directories recursively if specified.

---

## Installation

1. **Python Version**: Ensure you have Python 3.7 or higher installed.
2. **Dependencies**: Install the required dependencies using pip:
   ```bash
   pip install pillow
   ```

## Usage

Run the script from the command line with the following syntax:
```bash
python export_meta_data_json.py <directory> [options]
```
### Arguments

| Argument               | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `<directory>`          | The directory containing the image files to process.                        |
| `-r`, `--recursive`    | Traverse directories recursively.                                           |
| `-n`, `--dry-run`      | Simulate the process without modifying files.                               |
| `-f`, `--fix-filenames`| Fix floating-point numbers in filenames to have two digits after the decimal.|
| `--force-json`         | Force overwrite of JSON files even if they have already been processed.     |
| `-c`, `--clean`        | Delete orphaned `.json` and `.txt` files and empty directories.             |

## Examples

1. **Basic Usage**: Extract metadata from images in a directory.
    ```bash
    python export_meta_data_json.py /path/to/directory
    ```
2. **Recursive Processing**: Extract metadata from images in a directory and its subdirectories.
    ```bash
    python export_meta_data_json.py /path/to/directory -r
    ```
3. **Dry Run**: Simulate the process without modifying files.
    ```bash
    python export_meta_data_json.py /path/to/directory -n
    ```
4. **Fix Filenames**: Fix floating-point numbers in filenames and extract metadata
    ```bash
    python export_meta_data_json.py /path/to/directory -f
    ```
5. **Force JSON Overwrite**: Force overwrite of JSON files even if they have already been processed.
    ```bash
    python export_meta_data_json.py /path/to/directory --force-json
    ```
6. **Clean Orphaned Files**: Delete orphaned `.json` and `.txt` files and empty directories.
    ```bash
    python export_meta_data_json.py /path/to/directory -c
    ```
7. **Combined Options**: Recursively process images, fix filenames, and clean orphaned files.
    ```bash
    python export_meta_data_json.py /path/to/directory -r -f -c
    ```

## Output

* **Metadata Files**: Metadata is saved in `.txt` or `.json` files with the same name as the image file.
    * If the metadata is JSON-formatted, it is saved in a `.json` file.
    * If the metadata is not JSON-formatted, it is saved in a `.txt` file.

* **Merged JSON**: If a `.json` file already exists, the script merges the new metadata with the existing data, ensuring the `post_training_processing` array is updated.

* **Renamed Files**: If the `--fix-filenames` option is used, filenames with floating-point numbers are fixed to have two digits after the decimal point.

## Notes

* **Dry Run**: Use the `--dry-run` option to test the script without making any changes.

* **Orphaned Files**: The --clean option helps remove .json and .txt files that no longer have a corresponding image file.

## License

This script is provided under the MIT License. Feel free to modify and distribute it as needed.

# comfyui_export_metadata
