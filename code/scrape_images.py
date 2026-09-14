"""
scrape_images.py

Collects raw candidate images per class for the One Piece "Luffy's Gears"
fine-grained classification project — base form, Gear Second, Gear
Third, Gear Fourth (Boundman), Gear Fifth.

WHY better_bing_image_downloader (not icrawler):
  icrawler's GoogleImageCrawler and BingImageCrawler are both broken as
  of testing — Google crashes outright (JS-only page, no crawler can
  read it without a real browser), and Bing's crawler runs without
  crashing but returns unrelated images because its HTML parser is out
  of date against Bing's current layout.

  This script uses `better_bing_image_downloader` instead — actively
  maintained, hits Bing's JSON API directly instead of scraping rendered
  HTML. Bing is used as the ONLY engine; it already yields near-full
  results on its own (often 85-90+ out of a 90+ limit per query).

WHY THIS SET IS TRICKY:
  - Unlike the Iron Man armor set (where several suits share the same
    red/gold color scheme), Luffy's Gears are each visually VERY
    distinct by color/shape — so the hard part here isn't inter-class
    confusion, it's INTRA-class consistency:
  - Gear Fourth has THREE distinct sub-forms in canon: Boundman (the
    default, most common), Tankman, and Snakeman — they look quite
    different from each other. Queries below target Boundman only, on
    purpose, to keep this class visually consistent. Mixing all three
    sub-forms into one "gear4" class would make that single class more
    visually inconsistent than the other four classes.
  - Base Luffy ("gear1") appears across 1000+ episodes spanning multiple
    animation eras/studios with visibly different art quality — consider
    whether to restrict scraping to a specific era for consistency, or
    accept the variety as realistic (your call — flag it either way in
    the "dataset description" section of your presentation).
  - Gear Second/Third were introduced PRE-timeskip, Gear Fourth POST-
    timeskip, Gear Fifth very recently (Wano/Egghead arcs) — each gear's
    available footage skews toward a different animation era by nature
    of when it was introduced. Same caveat as above: worth mentioning,
    not necessarily worth "fixing."
  - Manga (black-and-white) results will slip into searches sometimes —
    decide upfront whether you want a color-only dataset (recommended,
    for consistency) and filter those out during manual review.
  - "Gear 1" is FAN terminology, not canon (there's no in-story "Gear
    First") — if you'd rather not include a base-form class at all,
    just delete the "gear1" entry below and go with 4 classes instead.

IMPORTANT — this script only DOWNLOADS CANDIDATES. You must still:
  1. Manually review and delete bad/irrelevant/duplicate images
  2. Pay extra attention to gear4 specifically — remove any Tankman/
     Snakeman images that slipped in if you're keeping it Boundman-only
  3. Decide on and enforce a manga-vs-anime-vs-fanart policy consistently
     across all 5 classes, not just some
  4. Keep a record of what search terms/sources you used per class,
     for the "Dataset description" section of your presentation

INSTALL:
    pip install better-bing-image-downloader

Usage:
    python scrape_images.py
"""

import os
import shutil
from better_bing_image_downloader import downloader

# ---- EDIT THIS: one or more search queries per class ----
CLASSES = {
    "gear1": [
        "Monkey D Luffy base form anime",
        "Luffy normal form One Piece screenshot",
        "Luffy straw hat character anime",
        "Luffy action figure normal form",
        "Luffy anime close up face",
        "Luffy full body normal form",
    ],
    "gear2": [
        "Luffy Gear Second anime",
        "Luffy Gear 2nd red skin steam",
        "One Piece Gear Second screenshot",
        "Luffy Gear Second action figure",
        "Luffy Gear 2 close up",
        "Luffy Gear Second full body",
    ],
    "gear3": [
        "Luffy Gear Third giant fist",
        "Luffy Gear 3rd bone balloon arm",
        "One Piece Gear Third screenshot",
        "Luffy Gear Third action figure",
        "Luffy Gigant Pistol Gear 3",
        "Luffy Gear Third full body",
    ],
    "gear4": [
        "Luffy Gear Fourth Boundman anime",
        "Luffy Gear 4 Boundman inflated muscle",
        "One Piece Gear Fourth Boundman screenshot",
        "Luffy Gear Fourth Boundman action figure",
        "Luffy Gear 4 black Haki armor Boundman",
        "Luffy Boundman close up",
    ],
    "gear5": [
        "Luffy Gear Fifth Nika anime",
        "Luffy Gear 5 white hair screenshot",
        "One Piece Gear Fifth Sun God Nika",
        "Luffy Gear Fifth action figure",
        "Luffy Gear 5 close up",
        "Luffy Gear Fifth full body",
    ],
}

# Raised from a smaller default -> 130 to increase the raw pool per class.
# Bing has been yielding near-full results in testing (often 95%+ of the
# limit), so this is a fairly direct increase in final dataset size, not
# just a theoretical ceiling.
IMAGES_PER_QUERY = 130           # per query
OUTPUT_ROOT = "raw_dataset"      # final images land in raw_dataset/<class_name>/
TEMP_ROOT = "_bbid_tmp"          # scratch space, cleaned up as we go
ENGINE = "bing"                  # Bing only — see note above


def scrape_class(class_name: str, queries: list[str]) -> int:
    class_dir = os.path.join(OUTPUT_ROOT, class_name)
    os.makedirs(class_dir, exist_ok=True)

    counter = 0
    for query in queries:
        print(f"[{class_name}] (bing) searching: '{query}'")
        try:
            downloader(
                query=query,
                limit=IMAGES_PER_QUERY,
                output_dir=TEMP_ROOT,
                engine=ENGINE,
                max_workers=8,
                verbose=False,
            )
        except Exception as e:
            # Don't let one bad query kill the whole run.
            print(f"  !! bing failed for '{query}': {e}")
            continue

        # better_bing_image_downloader saves into TEMP_ROOT/<query>/ —
        # move those files into the class folder with unique names,
        # then clean up the per-query temp folder.
        query_subdir = os.path.join(TEMP_ROOT, query)
        if not os.path.isdir(query_subdir):
            print(f"  (no results folder for '{query}' — skipping)")
            continue

        moved = 0
        for fname in os.listdir(query_subdir):
            src = os.path.join(query_subdir, fname)
            if not os.path.isfile(src):
                continue
            if fname.lower().endswith((".json", ".jsonl")):
                continue  # skip manifest files, keep only images
            ext = os.path.splitext(fname)[1] or ".jpg"
            dst = os.path.join(class_dir, f"{class_name}_{counter:05d}{ext}")
            shutil.move(src, dst)
            counter += 1
            moved += 1
        shutil.rmtree(query_subdir, ignore_errors=True)
        print(f"  -> moved {moved} images into {class_dir}")

    return counter


def main():
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    os.makedirs(TEMP_ROOT, exist_ok=True)

    totals = {}
    for class_name, queries in CLASSES.items():
        totals[class_name] = scrape_class(class_name, queries)

    shutil.rmtree(TEMP_ROOT, ignore_errors=True)

    print("\nDone. Raw candidates (Bing) are in:", OUTPUT_ROOT)
    print("\nImages collected per class (before cleaning):")
    for class_name, count in totals.items():
        print(f"  {class_name}: {count}")

    print("\nNEXT STEPS (do not skip these):")
    print("  1. Run dedupe_and_clean.py to remove exact/near duplicates")
    print("  2. Manually eyeball each class folder and delete irrelevant images")
    print("     (be extra careful with gear4 — remove any Tankman/Snakeman")
    print("      images that slipped in if you're keeping it Boundman-only)")
    print("  3. Decide on a manga-vs-anime-vs-fanart policy and apply it")
    print("     consistently across ALL FIVE classes, not just some")
    print("  4. If any class ends up noticeably smaller than the rest after")
    print("     cleaning, prioritize adding to it specifically rather than")
    print("     adding equally to every class")


if __name__ == "__main__":
    main()
