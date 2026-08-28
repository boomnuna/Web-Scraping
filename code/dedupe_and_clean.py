"""
dedupe_and_clean.py

Run this AFTER scrape_images.py.

Search-engine crawlers commonly return:
  - the same image multiple times (from different result pages)
  - corrupted / unreadable files
  - near-duplicates (same product photo, tiny crop/resize difference)

This script:
  1. Deletes files that fail to open as valid images
  2. Deletes exact duplicates (identical file hash)
  3. Flags near-duplicates (perceptually similar) for manual review —
     it does NOT auto-delete these, since two genuinely different USB
     connectors can look similar; you should eyeball the flagged pairs.

Usage:
    python dedupe_and_clean.py
"""

import os
import hashlib
from PIL import Image

try:
    import imagehash  # optional, for near-duplicate detection
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False

DATASET_ROOT = "raw_dataset"
NEAR_DUP_THRESHOLD = 5  # lower = stricter match (imagehash Hamming distance)


def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def clean_class_folder(class_dir: str):
    removed_corrupt = 0
    removed_exact_dup = 0
    seen_hashes = {}
    valid_files = []

    for fname in os.listdir(class_dir):
        fpath = os.path.join(class_dir, fname)

        # 1) validity check
        try:
            with Image.open(fpath) as img:
                img.verify()
        except Exception:
            os.remove(fpath)
            removed_corrupt += 1
            continue

        # 2) exact duplicate check
        h = file_hash(fpath)
        if h in seen_hashes:
            os.remove(fpath)
            removed_exact_dup += 1
            continue
        seen_hashes[h] = fpath
        valid_files.append(fpath)

    print(f"  removed {removed_corrupt} corrupt files, "
          f"{removed_exact_dup} exact duplicates, "
          f"{len(valid_files)} valid files remain")

    # 3) near-duplicate flagging (optional, only if imagehash is installed)
    if HAS_IMAGEHASH and len(valid_files) > 1:
        hashes = {}
        for fpath in valid_files:
            try:
                h = imagehash.phash(Image.open(fpath))
                hashes[fpath] = h
            except Exception:
                continue

        flagged_pairs = []
        files = list(hashes.keys())
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                diff = hashes[files[i]] - hashes[files[j]]
                if diff <= NEAR_DUP_THRESHOLD:
                    flagged_pairs.append((files[i], files[j], diff))

        if flagged_pairs:
            print(f"  {len(flagged_pairs)} near-duplicate pairs flagged for manual review:")
            for a, b, diff in flagged_pairs[:20]:  # don't spam if there are hundreds
                print(f"    {os.path.basename(a)}  <->  {os.path.basename(b)}  (distance={diff})")
            if len(flagged_pairs) > 20:
                print(f"    ... and {len(flagged_pairs) - 20} more")


def main():
    if not os.path.isdir(DATASET_ROOT):
        print(f"'{DATASET_ROOT}' not found — run scrape_images.py first.")
        return

    if not HAS_IMAGEHASH:
        print("Tip: install 'imagehash' (pip install imagehash) to also "
              "detect near-duplicate images, not just exact ones.\n")

    for class_name in os.listdir(DATASET_ROOT):
        class_dir = os.path.join(DATASET_ROOT, class_name)
        if not os.path.isdir(class_dir):
            continue
        print(f"Cleaning class '{class_name}'...")
        clean_class_folder(class_dir)


if __name__ == "__main__":
    main()
