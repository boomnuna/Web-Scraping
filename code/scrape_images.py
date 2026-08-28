"""
scrape_images.py

Collects raw candidate images per class using search-engine image crawlers
(Bing / Google via icrawler) instead of scraping a specific e-commerce site
directly. This is generally safer (no anti-bot walls, no ToS issues tied to
one retailer) and is the standard approach used in academic dataset
collection.

IMPORTANT — this script only DOWNLOADS CANDIDATES. You must still:
  1. Manually review and delete bad/irrelevant/duplicate images
     (search crawlers always return some noise/wrong results)
  2. Mix these with your OWN photos (different backgrounds/lighting) —
     see the assignment condition: you cannot rely on scraping alone
  3. Keep a record of what search terms/sources you used per class,
     for the "Dataset description" section of your presentation

Usage:
    python scrape_images.py
"""

import os
from icrawler.builtin import BingImageCrawler, GoogleImageCrawler

# ---- EDIT THIS: one or more search queries per class ----
# Multiple queries per class = more diversity (different brands/angles/contexts)
CLASSES = {
    "usb_type_a": [
        "USB type A connector close up",
        "USB-A cable head macro",
        "USB flash drive connector",
    ],
    "usb_type_b": [
        "USB Micro-B connector close up",
        "micro USB cable head macro",
        "android charging cable tip",
    ],
    "usb_type_c": [
        "USB-C connector close up",
        "USB type C cable head macro",
        "USB-C charging cable tip",
    ],
    "lightning": [
        "Apple Lightning connector close up",
        "iPhone lightning cable tip macro",
        "lightning charging cable head",
    ],
}

IMAGES_PER_QUERY = 120          # crawler will try to get this many per query, per engine
OUTPUT_ROOT = "raw_dataset"     # images land in raw_dataset/<class_name>/

# Which search engines to run. Both write into the SAME class folder, so
# results get merged automatically. icrawler auto-numbers filenames per
# engine run, so Bing's and Google's files won't overwrite each other.
ENGINES = {
    "bing": BingImageCrawler,
    "google": GoogleImageCrawler,
}


def scrape_class(class_name: str, queries: list[str]):
    class_dir = os.path.join(OUTPUT_ROOT, class_name)
    os.makedirs(class_dir, exist_ok=True)

    for engine_name, EngineClass in ENGINES.items():
        for query in queries:
            print(f"[{class_name}] ({engine_name}) searching: '{query}'")
            crawler = EngineClass(
                storage={"root_dir": class_dir},
                downloader_threads=4,
            )
            try:
                crawler.crawl(
                    keyword=query,
                    max_num=IMAGES_PER_QUERY,
                    filters=None,   # you can add e.g. {"size": "medium"} if needed
                )
            except Exception as e:
                # Google's crawler is more prone to breaking when the site
                # changes its page structure — don't let one failed query
                # kill the whole run, just log and move on.
                print(f"  !! {engine_name} failed for '{query}': {e}")


def main():
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    for class_name, queries in CLASSES.items():
        scrape_class(class_name, queries)

    print("\nDone. Raw candidates (Bing + Google merged) are in:", OUTPUT_ROOT)
    print("NEXT STEPS (do not skip these):")
    print("  1. Run dedupe_and_clean.py to remove exact/near duplicates")
    print("     (merging two engines means MORE duplicates than before —")
    print("      this step matters more now, not less)")
    print("  2. Manually eyeball each class folder and delete irrelevant images")
    print("  3. Add your own photographed images into the same class folders")


if __name__ == "__main__":
    main()
