import json
import csv
import glob
import os

rows = []


for file in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "extracted_data", "*.json")):
    with open(file) as f:
        d = json.load(f)

    if d["legal_property"] is None:
        d["legal_property"] = {
            "lot": "",
            "block": "",
            "section": ""
        }
    
    rows.append([
        d["docs_id"],
        d["grantor"],
        d["property_address"],
        d["legal_property"]["lot"],
        d["legal_property"]["block"],
        d["legal_property"]["section"]
    ])

with open("sheet_data.csv","w",newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "docs_id",
        "grantor",
        "property_address",
        "lot",
        "block",
        "section"
    ])

    writer.writerows(rows)