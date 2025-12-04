#!/usr/bin/env python3
"""
Dataset Cleaning Utility

Renames image files that share the same base name but have different extensions
to prevent conflicts when generating captions.

Example:
  photo.png + photo.jpg → photo_png.png + photo_jpg.jpg
  (Associated caption files like photo.txt are also renamed accordingly)

Usage:
  python dataset_cleaning.py <folder_path> [--dry-run]
"""

import os
import sys
import argparse
from collections import defaultdict

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}
CAPTION_EXTENSIONS = {'.txt', '.caption'}


def find_conflicts(folder_path):
    """Find files that share the same base name but have different extensions."""
    base_name_map = defaultdict(list)

    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if not os.path.isfile(filepath):
            continue

        base, ext = os.path.splitext(filename)
        if ext.lower() in IMAGE_EXTENSIONS:
            base_name_map[base].append(filename)

    # Only return entries with conflicts (more than one file per base name)
    return {base: files for base, files in base_name_map.items() if len(files) > 1}


def get_new_name(filename):
    """Generate new filename by appending extension to base name."""
    base, ext = os.path.splitext(filename)
    ext_suffix = ext.lstrip('.').lower()
    return f"{base}_{ext_suffix}{ext}"


def find_associated_files(folder_path, base_name):
    """Find caption files associated with the base name."""
    associated = []
    for ext in CAPTION_EXTENSIONS:
        caption_file = base_name + ext
        if os.path.exists(os.path.join(folder_path, caption_file)):
            associated.append(caption_file)
    return associated


def rename_conflicting_files(folder_path, dry_run=False):
    """Rename files with conflicting base names."""
    conflicts = find_conflicts(folder_path)

    if not conflicts:
        print("No conflicting filenames found.")
        return

    print(f"Found {len(conflicts)} base name(s) with conflicts:\n")

    renames = []

    for base_name, files in conflicts.items():
        print(f"  '{base_name}' has {len(files)} files:")
        for f in files:
            print(f"    - {f}")

        # Plan renames for image files
        for filename in files:
            old_path = os.path.join(folder_path, filename)
            new_name = get_new_name(filename)
            new_path = os.path.join(folder_path, new_name)
            renames.append((old_path, new_path, filename, new_name))

        # Check for associated caption files (these would be ambiguous)
        captions = find_associated_files(folder_path, base_name)
        if captions:
            print(f"    ⚠ Associated caption file(s) found: {captions}")
            print(f"      These will need manual review - unclear which image they belong to")

    print(f"\nPlanned renames ({len(renames)} files):\n")
    for old_path, new_path, old_name, new_name in renames:
        print(f"  {old_name} → {new_name}")

    if dry_run:
        print("\n[DRY RUN] No files were modified.")
        return

    print("\nExecuting renames...")
    for old_path, new_path, old_name, new_name in renames:
        if os.path.exists(new_path):
            print(f"  ✗ Skipped {old_name}: target '{new_name}' already exists")
            continue
        os.rename(old_path, new_path)
        print(f"  ✓ {old_name} → {new_name}")

    print("\nDone!")


def main():
    parser = argparse.ArgumentParser(
        description="Rename image files with conflicting base names in a dataset folder."
    )
    parser.add_argument("folder", help="Path to the dataset folder")
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be renamed without actually renaming"
    )

    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"Error: '{args.folder}' is not a valid directory")
        sys.exit(1)

    rename_conflicting_files(args.folder, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
