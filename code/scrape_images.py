"""
scrape_images.py

Collects raw candidate images per class for the Iron Man armor (MCU)
fine-grained classification project — War Machine, Mark III, Mark VI,
Mark L, Mark LXXXV, Hulkbuster.

WHY THIS VERSION IS DIFFERENT (read this first):
  The original version of this script used `icrawler`'s GoogleImageCrawler
  and BingImageCrawler. Both are broken as of testing:
    - GoogleImageCrawler crashes outright (`TypeError: 'NoneType' object
      is not iterable`) — this is a long-standing, unfixed bug going back
      to 2021 in the icrawler GitHub repo. Google now serves a
      JavaScript-only page to plain HTTP requests, so no HTML-scraping
      crawler can read it anymore without a real browser.
    - BingImageCrawler "ran" without crashing but returned completely
      unrelated images (random product photos, unrelated wallpapers) —
      its page parser is also out of date against Bing's current layout.

  This version uses `better_bing_image_downloader` instead, an actively
  maintained package (last updated June 2026) built specifically for ML
  dataset collection. It hits Bing's JSON API directly instead of
  scraping rendered HTML, which is why it still works.

  Bing is used as the ONLY engine here. It already yields near-full
  results on its own (often 85-90+ out of a 90 limit per query), and a
  DuckDuckGo pass was tried and dropped — it kept getting HTTP 403
  (rate-limited/blocked) and wasn't worth the added complexity for the
  extra images it wasn't reliably providing anyway.

WHY THIS SET IS TRICKY (unchanged from before):
  - Mark III and Mark VI are both red/gold "plated" armor — the model has
    to pick up on subtle plating/reactor differences, not just color.
  - Mark L and Mark LXXXV are both red/gold NANOTECH armor (smooth, no
    visible plate seams) — even harder to tell apart than III vs VI.
  - Hulkbuster has TWO visually different movie versions (Age of Ultron
    "Mark XLIV" vs Infinity War "Veronica"). Queries below target the
    Age of Ultron version specifically.
  - War Machine has THREE color schemes across films (classic gunmetal
    grey/black, and a red-white-blue "Iron Patriot" repaint in Iron Man 3).
    Queries below target the classic Avengers/Infinity War grey-black
    version specifically.

IMPORTANT — this script only DOWNLOADS CANDIDATES. You must still:
  1. Manually review and delete bad/irrelevant/duplicate images
  2. Pay extra attention to the two fine-grained pairs when reviewing:
     Mark III vs Mark VI, and Mark L vs Mark LXXXV
  3. Keep a record of what search terms/sources you used per class,
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
    "mark3": [
        "Iron Man Mark 3 armor",
        "Iron Man Mark III suit movie",
        "Tony Stark Mark 3 red gold armor",
        "Iron Man Mark 3 action figure",
        "Iron Man 2008 armor screenshot",
        "Iron Man Mark 3 close up helmet",
        "Iron Man Mark 3 side view armor",
    ],
    "mark6": [
        "Iron Man Mark 6 armor Avengers",
        "Iron Man Mark VI suit",
        "Tony Stark Mark 6 triangle arc reactor",
        "Iron Man Mark 6 action figure",
        "The Avengers 2012 Iron Man armor",
        "Iron Man Mark 6 close up helmet",
        "Iron Man Mark 6 side view armor",
    ],
    "mark50": [
        "Iron Man Mark 50 nanotech armor",
        "Iron Man Mark L Infinity War suit",
        "Tony Stark nanotech suit Infinity War",
        "Iron Man Mark 50 action figure",
        "Avengers Infinity War Iron Man armor screenshot",
        "Iron Man Mark 50 close up helmet",
        "Iron Man Mark 50 side view armor",
    ],
    "mark85": [
        "Iron Man Mark 85 armor Endgame",
        "Iron Man Mark LXXXV suit",
        "Tony Stark final armor Endgame",
        "Iron Man Mark 85 action figure",
        "Avengers Endgame Iron Man armor screenshot",
        "Iron Man Mark 85 close up helmet",
        "Iron Man Mark 85 side view armor",
    ],
    "hulkbuster": [
        "Hulkbuster Mark 44 Age of Ultron",
        "Iron Man Hulkbuster armor Age of Ultron movie",
        "Hulkbuster suit Tony Stark Avengers 2",
        "Hulkbuster Mark 44 action figure",
        "Avengers Age of Ultron Hulkbuster screenshot",
        "Hulkbuster Mark 44 close up helmet",
        "Hulkbuster Mark 44 full body armor",
    ],
    "war_machine": [
        "War Machine armor Avengers Infinity War",
        "War Machine suit grey black Avengers",
        "James Rhodes War Machine armor movie",
        "War Machine action figure grey armor",
        "Avengers War Machine screenshot",
        "War Machine close up helmet",
        "War Machine side view armor",
    ],
}

# Raised from 90 -> 130 to increase the raw pool per class. Bing has been
# yielding near-full results in testing (often 95%+ of the limit), so
# this is a fairly direct increase in final dataset size, not just a
# theoretical ceiling.
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
    print("     (be extra careful with mark3/mark6 getting mixed up, and")
    print("      mark50/mark85 getting mixed up — they're the fine-grained")
    print("      pairs this whole project is testing)")
    print("  3. Double-check hulkbuster folder has no Infinity War 'Veronica'")
    print("     version images, and war_machine has no Iron Patriot")
    print("     red-white-blue images")
    print("  4. If any class ends up noticeably smaller than the rest after")
    print("     cleaning, prioritize adding to it specifically rather than")
    print("     adding equally to every class")


if __name__ == "__main__":
    main()
