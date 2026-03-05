import os
import re

from flask import json

# ----------------------------
# DOCS ID
# ----------------------------
def get_docs_id(filename):
    name = os.path.splitext(filename)[0]
    return name

# ----------------------------
# GRANTOR EXTRACTION
# ----------------------------
import re
from pathlib import Path


def clean_name(name):
    name = name.replace("\n", " ")
    name = re.sub(r"\s+", " ", name)

    # remove descriptors
    name = re.sub(
        r",?\s*(AS COMMUNITY PROPERTY|WIFE AND HUSBAND|UNMARRIED|A SINGLE MAN|A MARRIED WOMAN).*",
        "",
        name,
        flags=re.IGNORECASE
    )

    return name.strip()

def extract_grantor(text):

    # -------- Pattern 1 (multi-line after Grantor label) --------
    pattern1 = re.search(
        r"Grantor\(s\)/Mortgagor\(s\):\s*(.*?)\n\s*(?:Original|LEGAL|Recorded|Property)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if pattern1:
        return clean_name(pattern1.group(1))

    # -------- Pattern 2 (executed by NAME) --------
    pattern2 = re.search(
        r"executed by\s+([A-Z0-9 ,.&'\-\n]+)",
        text,
        re.IGNORECASE
    )

    if pattern2:
        return clean_name(pattern2.group(1))

    # -------- Pattern 3 (NAME as Grantor/Borrower) --------
    pattern3 = re.search(
        r"([A-Z][A-Z ,.&'\-\n]+?)\s+as\s+Grantor/Borrower",
        text,
        re.IGNORECASE
    )

    if pattern3:
        return clean_name(pattern3.group(1))

    return None


def clean_grantor(name):

    name = name.strip(" ,.")

    # OCR fixes
    name = name.replace(" Ill", " III")

    # collapse spacing
    name = " ".join(name.split())

    return name

# ----------------------------
# PROPERTY ADDRESS
# ----------------------------

import re

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


def clean(addr):
    addr = addr.replace("\n", " ")
    addr = re.sub(r"\s+", " ", addr)
    return addr.strip()


def extract_address(text):

    # -------- CASE 1: Commonly known as --------
    m = re.search(
        r"Commonly known as:\s*([^\n]+)",
        text,
        re.IGNORECASE
    )

    if m:
        addr = clean(m.group(1))
        if not is_ignored(addr):
            return addr

    # -------- CASE 2: street address line --------
    for line in text.splitlines():

        line = line.strip()

        if re.match(r"\d{3,6}\s+.*TX\s*\d{5}", line, re.IGNORECASE):

            if not is_ignored(line):
                return clean(line)

    # ---------------------------
    # CASE 3: Property address block (FRCL-2026-25 format)
    # ---------------------------
    m = re.search(
        r"Property address:\s*(.*?)\n\s*([A-Z ]+,\s*TX\s*\d{5})",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if m:

        street_block = m.group(1)

        # Find the street number inside the block (ignores the date)
        street_match = re.search(r"\d{3,6}\s+[A-Z0-9 .]+", street_block)

        if street_match:

            addr = clean(street_match.group(0) + " " + m.group(2))

            if not is_ignored(addr):
                return addr
    
    return ""

# ----------------------------
# LOT/BLOCK EXTRACTION
# ----------------------------
def word_to_number(word):

    word = word.upper().replace("-", " ")

    units = {
        "ZERO":0,"ONE":1,"TWO":2,"THREE":3,"FOUR":4,"FIVE":5,"SIX":6,
        "SEVEN":7,"EIGHT":8,"NINE":9,"TEN":10,"ELEVEN":11,"TWELVE":12,
        "THIRTEEN":13,"FOURTEEN":14,"FIFTEEN":15,"SIXTEEN":16,
        "SEVENTEEN":17,"EIGHTEEN":18,"NINETEEN":19
    }

    tens = {
        "TWENTY":20,"THIRTY":30,"FORTY":40,"FIFTY":50,
        "SIXTY":60,"SEVENTY":70,"EIGHTY":80,"NINETY":90
    }

    total = 0

    for part in word.split():
        if part in units:
            total += units[part]
        elif part in tens:
            total += tens[part]

    return total if total > 0 else None

def extract_lot_block_section(text):
    
    # First try: Legal Description block
    m = re.search(
        r"Legal Description:\s*(.*?)(?:\n\n|In accordance|WHEREAS|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not m:
        # fallback for other format
        m = re.search(
            r"\bLot\s+.*?Harris County, Texas",
            text,
            re.IGNORECASE | re.DOTALL
        )

    if not m:
        return None

    legal = m.group(0)

    lot = None
    block = None
    section = None

    lot_match = re.search(r"\bLot\s+([A-Z0-9\(\)\-]+)", legal, re.IGNORECASE)
    block_match = re.search(r"\bBlock\s+([A-Z0-9\(\)\-]+)", legal, re.IGNORECASE)
    section_match = re.search(
        r"\b(?:Section|Sec\.?|SEC\.?)\s+([A-Z0-9\(\)\-]+)",
        legal,
        re.IGNORECASE
    )

    if lot_match:
        lot = lot_match.group(1)

    if block_match:
        block = block_match.group(1)

    if section_match:
        section = section_match.group(1)

    if not lot.isdigit():
        lot = word_to_number(lot)
    
    if not block.isdigit():
        block = word_to_number(block)
    
    if not section.isdigit():
        section = word_to_number(section)
    
    return {
        "lot": int(lot),
        "block": int(block),
        "section": int(section)
    }
        

# ----------------------------
# MAIN PROCESS
# ----------------------------
def process_file(filepath):

    filename = os.path.basename(filepath)
    docs_id = get_docs_id(filename)

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    grantor = extract_grantor(text)
    address = extract_address(text)

    lot_info = None
    
    if (address == ""):
        lot_info = extract_lot_block_section(text)
    
    return {
        "docs_id": docs_id,
        "grantor": grantor,
        "property_address": address,
        "legal_property": lot_info
    }


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    for file in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleaned_texts")):
        if file.endswith(".txt"):
            print(f"Processing: {file}")
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleaned_texts", file)
            data = process_file(file_path)
            
            save_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "extracted_data", f"{data['docs_id']}.json"
            )
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"Extracted data saved to: {save_path}")