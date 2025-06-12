# FPDS Scrape

This project contains a simple scraper for FPDS contract URLs.

## Requirements

- Python 3.8+
- Packages listed in `requirements.txt` (`requests` and `beautifulsoup4`)

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Provide a CSV file containing FPDS URLs (one per line) and specify an output file:

```bash
python scrape_fpds.py input.csv output.csv
```

For a quick demonstration you can use the included `first40.csv` which contains a small subset of URLs:

```bash
python scrape_fpds.py first40.csv demo_output.csv
```
