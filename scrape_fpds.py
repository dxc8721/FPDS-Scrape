import csv
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# fields that are always captured from each page
BASE_FIELDS = [
    "url",
    "action_obligation",
    "base_and_exercised_options_value",
    "base_and_all_options_value",
    "naics_code",
    "naics_code_description",
]

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
    data = {
        "url": url,
        "action_obligation": get_value("obligatedAmount"),
        "base_and_exercised_options_value": get_value("baseAndExercisedOptionsValue"),
        "base_and_all_options_value": get_value("ultimateContractValue"),
        "naics_code": get_value("principalNAICSCode"),
        "naics_code_description": get_value("NAICSCodeDescription"),
    }

    socio = soup.find(id="socio")
    if socio:
        for cb in socio.find_all("input", {"type": "checkbox"}):
            fid = cb.get("id")
            if not fid:
                continue
            hid = socio.find("input", {"id": f"pJS{fid}"})
            if hid and hid.has_attr("value"):
                data[fid] = hid["value"].strip()
            else:
                data[fid] = "true" if cb.has_attr("checked") else "false"
    return data

def main():
    import sys
    csv_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    urls = parse_urls(csv_path)

    rows = []
    socio_fields = set()
    for idx, url in enumerate(urls, 1):
        try:
            data = scrape_page(url)
        except Exception:
            data = {
                "url": url,
                "action_obligation": "ERROR",
                "base_and_exercised_options_value": "ERROR",
                "base_and_all_options_value": "ERROR",
                "naics_code": "ERROR",
                "naics_code_description": "ERROR",
            }
        socio_fields.update(k for k in data.keys() if k not in BASE_FIELDS)
        rows.append(data)
        if idx % 50 == 0:
            print(f"Processed {idx}/{len(urls)}")

    fieldnames = BASE_FIELDS + sorted(socio_fields)

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({fn: row.get(fn, "") for fn in fieldnames})

if __name__ == "__main__":
    main()
