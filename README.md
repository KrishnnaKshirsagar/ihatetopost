# Automated Quote-to-Instagram Poster

Generates textured, handwritten-style quote cards (1080×1350) with `-ff` in the bottom-right corner using quotes from [ZenQuotes](https://zenquotes.io/), and posts them automatically to Instagram via the official Meta Instagram Graph API on a GitHub Actions schedule.

## Project Structure

- `src/config.py` — Palettes (`cobalt_white`, `mustard_ink`, `charcoal_red`, `forest_cream`, `terracotta_cream`, `paper_ink`) and environment configuration
- `src/quotes.py` — Fetches quotes from ZenQuotes and deduplicates via `data/posted_quotes.json`
- `src/generator.py` — Renders textured cardstock backgrounds, wrapped handwritten typography (`assets/fonts/ShortStack-Regular.ttf`), and `-ff` signature
- `src/uploader.py` — Uploads the generated image to ImgBB or Cloudinary for a public HTTPS URL (required by Instagram Graph API)
- `src/instagram.py` — Publishes the image to Instagram via Meta Graph API (`v21.0`)
- `.github/workflows/post_quote.yml` — Daily scheduled GitHub Actions workflow

## Local Testing (Dry Run)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate a sample image in output/ without posting
python -m src.main --dry-run
```

Optional flags:
- `--palette cobalt_white` (or `mustard_ink`, `charcoal_red`, `forest_cream`, `terracotta_cream`, `paper_ink`)
- `--quote "Your custom quote" --author "Author Name"`
- `--signature "-ff"`

## GitHub Actions Setup

1. **Instagram Business/Creator Account**
   - Convert your Instagram account to **Business** or **Creator** and link it to a Facebook Page.
   - Create a Meta App in [Meta for Developers](https://developers.facebook.com/) with `instagram_basic`, `instagram_content_publish`, and `pages_show_list` permissions.
   - Obtain your **Instagram User ID** (`IG_USER_ID`) and a **Long-Lived Access Token** (`IG_ACCESS_TOKEN`).

2. **Public Image Host (pick one)**
   - **ImgBB (easiest)**: Get a free API key at [api.imgbb.com](https://api.imgbb.com/) → set `IMGBB_API_KEY`.
   - **Cloudinary**: Set `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET`.

3. **Add Repository Secrets**
   In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**:
   - `IG_USER_ID`
   - `IG_ACCESS_TOKEN`
   - `IMGBB_API_KEY` *(or the three `CLOUDINARY_*` secrets)*

4. **Test via GitHub Actions**
   Go to **Actions → Daily Quote to Instagram → Run workflow** (you can toggle `dry_run: true` first to inspect the generated image artifact before posting live).
