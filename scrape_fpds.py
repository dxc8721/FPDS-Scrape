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
    "award_type",
    "reason_for_modification",
    "type_of_contract",
    "labor_standards",
    "additional_reporting",
    "product_or_service_code",
    "product_or_service_code_description",
    "type_of_set_aside",
    "type_of_set_aside_source",
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
    def get_text(field_id: str):
        tag = soup.find(id=field_id)
        return tag.get_text(strip=True) if tag else ""
    def get_select(field_id: str):
        sel = soup.find(id=field_id)
        if sel:
            opt = sel.find("option", selected=True)
            if opt:
                return opt.get_text(strip=True)
        return ""
    def get_multiselect(field_id: str):
        sel = soup.find(id=field_id)
        if sel:
            vals = [opt.get_text(strip=True) for opt in sel.find_all("option") if opt.has_attr("selected")]
            return ";".join(vals)
        return ""
    data = {
        "url": url,
        "action_obligation": get_value("obligatedAmount"),
        "base_and_exercised_options_value": get_value("baseAndExercisedOptionsValue"),
        "base_and_all_options_value": get_value("ultimateContractValue"),
        "naics_code": get_value("principalNAICSCode"),
        "naics_code_description": get_value("NAICSCodeDescription"),
        "award_type": get_text("displayAwardType"),
        "reason_for_modification": get_value("reasonForModification"),
        "type_of_contract": get_select("typeOfContractPricing"),
        "labor_standards": get_select("laborStandards"),
        "additional_reporting": get_multiselect("listOfAdditionalReportingValues"),
        "product_or_service_code": get_value("productOrServiceCode"),
        "product_or_service_code_description": get_value("productOrServiceCodeDescription"),
        "type_of_set_aside": get_select("typeOfSetAside"),
        "type_of_set_aside_source": get_value("typeOfSetAsideSource"),
    }

    def parse_section(section):
        fields = {}
        if not section:
            return fields
        for cb in section.find_all("input", {"type": "checkbox"}):
            fid = cb.get("id")
            if not fid:
                continue
            tr = cb.find_parent("tr")
            label = ""
            if tr:
                cells = tr.find_all("td")
                if cells:
                    label = cells[-1].get_text(strip=True)
            if not label:
                label = cb.get("title", fid)
            hid = section.find("input", {"id": f"pJS{fid}"})
            if hid and hid.has_attr("value"):
                fields[label] = hid["value"].strip()
            else:
                fields[label] = "true" if cb.has_attr("checked") else "false"
        return fields

    socio = soup.find(id="socio")
    cert = soup.find(id="cert")

    for name, value in parse_section(socio).items():
        data[name] = value
    for name, value in parse_section(cert).items():
        data[name] = value
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
                "award_type": "ERROR",
                "reason_for_modification": "ERROR",
                "type_of_contract": "ERROR",
                "labor_standards": "ERROR",
                "additional_reporting": "ERROR",
                "product_or_service_code": "ERROR",
                "product_or_service_code_description": "ERROR",
                "type_of_set_aside": "ERROR",
                "type_of_set_aside_source": "ERROR",
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
