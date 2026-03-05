import re
import os
from pathlib import Path

from flask import json

IGNORED_ADDRESSES = [
    "9401 knight",
    "bayou city event center",
    "magnolia south ballroom",
    "harris county courthouse"
]


def normalize(text):
    return re.sub(r"[^\w\s]", "", text.lower())


def is_ignored(addr):

    addr_norm = normalize(addr)

    for bad in IGNORED_ADDRESSES:
        if bad in addr_norm:
            return True

    return False


def clean(text):

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_case_number(text):

    m = re.search(r"FRCL-\d{4}-\d+", text)

    if m:
        return m.group(0)

    return None


def extract_sale_date(text):

    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2},\s+\d{4}", text)

    if m:
        return m.group(0)

    return None


def extract_grantor(text):

    # Pattern 1
    m = re.search(r"Grantor\(s\)/Mortgagor\(s\):\s*(.*?)\n", text, re.IGNORECASE)

    if m:
        return clean(m.group(1))

    # Pattern 2
    m = re.search(r"([A-Z][A-Z ,.'-]+)\s+as\s+Grantor/Borrower", text)

    if m:
        return clean(m.group(1))

    # Pattern 3
    m = re.search(r"executed by\s+([A-Z0-9 ,.'-]+)", text, re.IGNORECASE)

    if m:
        return clean(m.group(1))

    return None


def extract_address(text):

    # Case 1: Commonly known as
    m = re.search(r"Commonly known as:\s*([^\n]+)", text, re.IGNORECASE)

    if m:
        addr = clean(m.group(1))
        if not is_ignored(addr):
            return addr


    # Case 2: standalone address line
    for line in text.splitlines():

        line = line.strip()

        if re.match(r"\d{3,6}\s+.*TX\s*\d{5}", line, re.IGNORECASE):

            if not is_ignored(line):
                return clean(line)


    # Case 3: Property address block
    m = re.search(
        r"Property address:\s*(.*?)\n\s*([A-Z ]+,\s*TX\s*\d{5})",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if m:

        street_match = re.search(r"\d{3,6}\s+[A-Z0-9 .]+", m.group(1))

        if street_match:

            addr = clean(street_match.group(0) + " " + m.group(2))

            if not is_ignored(addr):
                return addr

    return None


def parse_document(text):

    return {

        "case_number": extract_case_number(text),
        "grantor": extract_grantor(text),
        "address": extract_address(text),
        "sale_date": extract_sale_date(text)
    }


def process_folder(folder):

    for file in Path(folder).glob("*.txt"):
        
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        data = parse_document(text)

        save_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "extracted_data1", f"{file.name}.json"
        )
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

print("Processing documents...")
folder_path = "C:\\Users\\Fearl\\Documents\\GitHub\\RandomWorkStuff\\NeenoStuff\\cleaned_texts"
process_folder(folder_path)
print("Done.")