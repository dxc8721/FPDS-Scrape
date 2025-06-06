import csv
from pathlib import Path
import requests
from bs4 import BeautifulSoup

def parse_urls(csv_path: Path):
    urls = []
    current = ""
    with open(csv_path, newline='') as f:
        for line in f:
            line = line.strip()
            if line.startswith("http"):
                if current:
                    urls.append(current)
                current = line
            else:
                current += line
    if current:
        urls.append(current)
    # remove header if needed
    if urls and not urls[0].startswith("http"):
        urls.pop(0)
    return urls

def scrape_page(url: str):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    def get_value(field_id: str):
        tag = soup.find(id=field_id)
        if tag and tag.has_attr("value"):
            return tag["value"].strip()
        return ""
    return {
        "url": url,
        "action_obligation": get_value("obligatedAmount"),
        "base_and_exercised_options_value": get_value("baseAndExercisedOptionsValue"),
        "base_and_all_options_value": get_value("ultimateContractValue"),
    }

def main():
    import sys
    csv_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    urls = parse_urls(csv_path)
    with open(out_path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "url",
            "action_obligation",
            "base_and_exercised_options_value",
            "base_and_all_options_value",
        ])
        writer.writeheader()
        for idx, url in enumerate(urls, 1):
            try:
                data = scrape_page(url)
            except Exception as e:
                data = {
                    "url": url,
                    "action_obligation": "ERROR",
                    "base_and_exercised_options_value": "ERROR",
                    "base_and_all_options_value": "ERROR",
                }
            writer.writerow(data)
            if idx % 50 == 0:
                print(f"Processed {idx}/{len(urls)}")

if __name__ == "__main__":
    main()
