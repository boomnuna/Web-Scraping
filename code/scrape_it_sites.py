"""
scrape_it_sites.py

Scrapes product images directly from Thai IT retailer category/listing
pages (as opposed to scrape_images.py, which uses Bing/Google search).

WHY THIS EXISTS ALONGSIDE scrape_images.py:
Search engines return images from anywhere (blogs, forums, stock photos).
Scraping a retailer's own category page instead gets you images that are
guaranteed to be *product photos of the exact connector type*, all in a
consistent clean style — useful for boosting a class that's underrepresented
after the search-engine pass.

CONFIRMED WORKING: JIB (jib.co.th) — the config below was built by
inspecting an actual JIB category page, so it should work as-is.

NEEDS VERIFICATION: Banana IT and Advice — I don't have a verified page
structure for these two, so their configs below are TEMPLATES. Before
running them: open the category page in your browser, right-click a
product image -> "Inspect", and check that the image URL still contains
something like "/product/" in the path (adjust IMG_URL_MUST_CONTAIN if
not). If it breaks, that just means the site changed its HTML since this
was written — normal for scrapers, not a bug in your code.

LEGAL/ETHICAL NOTES (read before running):
  - This is for educational/coursework data collection, not redistribution
    or commercial use.
  - Respects a basic rate limit (REQUEST_DELAY_SECONDS) — do not lower this
    a lot, it's what keeps you from getting IP-blocked or hitting the site
    unfairly hard.
  - Always check <site>/robots.txt yourself before scraping a new site —
    this script does not auto-check it for you.
  - If a site starts returning errors/CAPTCHAs, stop — that's the site
    telling you to slow down or use their official API/search instead.

Usage:
    python scrape_it_sites.py
"""

import os
import re
import time
import requests
from urllib.parse import urljoin

OUTPUT_ROOT = "raw_dataset"
REQUEST_DELAY_SECONDS = 2.0   # politeness delay between page fetches
IMAGES_PER_CATEGORY_PAGE_LIMIT = 200  # safety cap per category URL

HEADERS = {
    # A normal browser user-agent avoids being blocked purely for looking
    # like a bare script. This is standard practice, not evasion of any
    # login/paywall — these are public product listing pages.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# ---- EDIT THIS: map each class to one or more category page URLs ----
# CONFIRMED (JIB): verified structure as of writing this script.
# TEMPLATE (Banana IT / Advice): verify selectors before relying on these.
SITE_CONFIGS = [
    {
        "site_name": "jib",
        "class_name": "usb_type_c",
        "category_urls": [
            "https://www.jib.co.th/web/product/product_list/3/1675",  # สายชาร์จ USB-C
        ],
        "img_url_must_contain": "/img_master/product/",
        "next_page_pattern": None,  # set per-site if you want to paginate
    },
    {
        "site_name": "jib",
        "class_name": "lightning",
        "category_urls": [
            "https://www.jib.co.th/web/product/product_list/3/1676",  # สายชาร์จ Lightning (Apple)
        ],
        "img_url_must_contain": "/img_master/product/",
        "next_page_pattern": None,
    },
    {
        "site_name": "jib",
        "class_name": "usb_type_b",
        "category_urls": [
            "https://www.jib.co.th/web/product/product_list/3/1674",  # สายชาร์จ Micro USB
        ],
        "img_url_must_contain": "/img_master/product/",
        "next_page_pattern": None,
    },
    # --- TEMPLATE: Banana IT (VERIFY BEFORE USE) ---
    # {
    #     "site_name": "bananait",
    #     "class_name": "usb_type_c",
    #     "category_urls": [
    #         "https://www.banana.co.th/th/search?q=USB-C",  # placeholder, verify real search/category URL
    #     ],
    #     "img_url_must_contain": "/media/",  # placeholder, verify real image path pattern
    #     "next_page_pattern": None,
    # },
    # --- TEMPLATE: Advice (VERIFY BEFORE USE) ---
    # {
    #     "site_name": "advice",
    #     "class_name": "usb_type_c",
    #     "category_urls": [
    #         "https://www.advice.co.th/search?keyword=USB-C",  # placeholder, verify real category URL
    #     ],
    #     "img_url_must_contain": "/images/",  # placeholder, verify real image path pattern
    #     "next_page_pattern": None,
    # },
]

IMG_TAG_PATTERN = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)


def fetch_page(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  !! failed to fetch {url}: {e}")
        return None


def extract_image_urls(html: str, base_url: str, must_contain: str) -> list[str]:
    urls = []
    for match in IMG_TAG_PATTERN.finditer(html):
        src = match.group(1)
        if must_contain in src:
            urls.append(urljoin(base_url, src))
    # de-dup while preserving order
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def download_image(url: str, dest_path: str) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return True
    except requests.RequestException as e:
        print(f"    !! failed to download {url}: {e}")
        return False


def scrape_config(config: dict):
    site_name = config["site_name"]
    class_name = config["class_name"]
    class_dir = os.path.join(OUTPUT_ROOT, class_name)
    os.makedirs(class_dir, exist_ok=True)

    downloaded = 0
    for category_url in config["category_urls"]:
        print(f"[{class_name}] ({site_name}) fetching: {category_url}")
        html = fetch_page(category_url)
        time.sleep(REQUEST_DELAY_SECONDS)
        if html is None:
            continue

        img_urls = extract_image_urls(html, category_url, config["img_url_must_contain"])
        print(f"  found {len(img_urls)} candidate image URLs")

        for i, img_url in enumerate(img_urls[:IMAGES_PER_CATEGORY_PAGE_LIMIT]):
            ext = os.path.splitext(img_url.split("?")[0])[1] or ".jpg"
            fname = f"{site_name}_{class_name}_{downloaded:04d}{ext}"
            dest_path = os.path.join(class_dir, fname)

            if download_image(img_url, dest_path):
                downloaded += 1
            time.sleep(REQUEST_DELAY_SECONDS)

    print(f"[{class_name}] ({site_name}) done — downloaded {downloaded} images\n")


def main():
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    for config in SITE_CONFIGS:
        scrape_config(config)

    print("Done. Remember to run dedupe_and_clean.py next, and to manually")
    print("review images — product listing thumbnails sometimes include")
    print("unrelated accessories bundled in the same photo.")


if __name__ == "__main__":
    main()
