# USB Connector Dataset Scraper

Collects raw candidate images for a USB connector classifier
(Type-A / Type-B(Micro) / Type-C / Lightning) using search-engine image
crawling, then cleans duplicates/corrupt files.

## Why search-engine crawling instead of scraping one e-commerce site?

- No anti-bot walls or ToS friction tied to a specific retailer
  (Shopee/Lazada/Amazon actively block scrapers)
- Naturally aggregates images across many brands/sellers/photo styles
  in one go
- Standard, widely-used approach for academic dataset collection
  (`icrawler` is a common research tool for exactly this)

**This still isn't a complete dataset by itself** — see "Required next
steps" below. The assignment explicitly requires you to *not* just use
existing/scraped images with zero additional collection effort.

## Setup

```bash
pip install -r requirements.txt
pip install imagehash   # optional, enables near-duplicate detection
```

## Workflow

```bash
# 1. Download raw candidates (edit CLASSES/queries in the script first)
python scrape_images.py

# 2. Remove corrupt files + exact duplicates, flag near-duplicates
python dedupe_and_clean.py

# 3. MANUALLY review raw_dataset/<class>/ folders:
#    - delete wrong/irrelevant results (crawlers are noisy)
#    - delete near-duplicates flagged in step 2 that are truly redundant
#    - check class balance (roughly similar image counts per class)

# 4. Add your own photographed images into the same class folders
#    (different backgrounds, lighting, angles — see the note below)
```

## Required next steps (don't skip — these matter for grading)

1. **Manual review is mandatory.** Search crawlers return wrong results
   (wrong connector type, unrelated products, watermarked stock photos).
   Budget real time for this — expect to keep maybe 60-80% of what's
   downloaded.

2. **Mix in your own photos.** Scraped images are heavily biased toward
   clean white-background product shots. Add photos you take yourselves
   with varied backgrounds/lighting so the model doesn't just learn
   "white background = usable image." This is also literally required by
   the assignment (dataset must show real additional collection effort,
   not just aggregated existing sources).

3. **Log your sources.** Keep a simple `sources.md` or spreadsheet noting
   which classes came from scraping vs. own photography vs. any public
   dataset, and roughly what proportion — you need this for the "Dataset
   description" section of your presentation (where data came from, bias
   considerations).

4. **Check class balance after cleaning.** If one class ends up with far
   fewer usable images than others (commonly Lightning or Micro-B, since
   they're less common now), either scrape more queries for that class or
   photograph more of your own to balance it — and if you can't fully
   balance it, that's fine, just report the imbalance and your handling
   strategy (the assignment explicitly asks for this).

## Adjusting search queries

Edit the `CLASSES` dict in `scrape_images.py` — add more query variants
per class (different phrasing, brand names, contexts like "charging
cable" vs "data cable") to get more diverse results. More/varied queries
generally beats cranking `IMAGES_PER_QUERY` very high on one query, since
a single query tends to plateau into near-identical results after a
point.

## Rate limiting / politeness

`icrawler`'s Bing crawler already paces requests reasonably by default.
Don't run many parallel crawler instances at once or crank
`downloader_threads` way up — that's what actually risks getting your IP
temporarily blocked by the search engine, not the modest volumes used
here.
