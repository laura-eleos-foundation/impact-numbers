import os
from pypdf import PdfReader
from flask import Flask, render_template
import re
from datetime import datetime
import calendar

order_numbers = {}
items_dict = {"pads": {"quantity": 0.00, "total_prices": 0.00},
             "tampons": {"quantity": 0.00, "total_prices": 0.00},
             "undies": {"quantity": 0.00, "total_prices": 0.00},
             "bras": {"quantity": 0.00, "total_prices": 0.00},
             "dental": {"quantity": 0.00, "total_prices": 0.00},
             "shower": {"quantity": 0.00, "total_prices": 0.00},
             "socks": {"quantity": 0.00, "total_prices": 0.00},
             "other": {"quantity": 0.00, "total_prices": 0.00}}
months_dict = {"january": items_dict,
          "february": items_dict,
          "march": items_dict,
          "april": items_dict,
          "may": items_dict,
          "june": items_dict,
          "july": items_dict,
          "august": items_dict,
          "september": items_dict,
          "october": items_dict,
          "november": items_dict,
          "december": items_dict
          }

years = ["2025", "2026"]
months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
data = ["quantity", "total_prices"]
items = ["pads", "tampons", "undies", "bras", "dental", "shower","socks", "other"]
data_dict = {"quantity": 0.00, "total_prices": 0.00}
years_totals = {}
for year in years:
    years_totals[year] = months_dict.copy()
    for month in months:
        years_totals[year][month] = items_dict.copy()
        for item in items:
            years_totals[year][month][item] = data_dict.copy()
            for track in data:
                years_totals[year][month][item][track] = 0.00

app = Flask(__name__)

def extract_items_from_text(text, filename):
    """
    Parses the raw text to find items and their quantities.
    Handles two common Amazon receipt text layouts.
    """
    items = []
    month = ""
    year = ""

    file_name_match = re.search(r'(.*?)(.pdf)', filename, re.IGNORECASE)
    #print(file_name_match.group(1))
    date_match = re.search(r'(Order placed)(.*?)(?=\n|\$Amazon.com order number)', text, re.IGNORECASE)
    if date_match:
        #print(date_match.group(2))
        order_numbers[date_match.group(2)] = file_name_match.group(1)
        splitSpace= date_match.group(2).split(" ")
        if splitSpace[3] == "Order":
            month = splitSpace[0]
            year = splitSpace[2]
        else:
            month = splitSpace[1]
            year = splitSpace[3]

    if month == '':
        #get 2nd page date format DD/MM/YY
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
        if date_match:
            split_date = date_match.group(1).split("/")
            month_num = split_date[0]
            month = calendar.month_name[int(month_num)]
            year = "20" + split_date[2]

    # --- Strategy A: "1 of: Item Name" format ---
    # Common in "Order Details" views
    strategy_a_matches = list(re.finditer(r'(\d+)\s+of:\s+(.*?)(?=\n|\$|Sold by)(\$\d+\.\d{2})', text, re.IGNORECASE))
    pattern = re.compile(r'(\d+)\s+of:\s+(.*?).(?=\n|\$|Sold by)*?(\$\d+\.\d{2})', re.DOTALL)
    matches = pattern.findall(text)
    if len(matches) > 0:
        for match in matches:
            #print(match)
            qty = match[0]
            desc = match[1].strip()
            price = match[2]
            desc = re.sub(r'\s+', ' ', desc)
            items.append((qty, desc, price, month, year))
        return items

    # --- Strategy B: "Printer Friendly" format ---
    # Pattern: Description -> Sold by -> Price -> [Optional Qty Number] -> Next Description
    # We split the text by "Sold by:" markers to isolate blocks.

    # 1. Normalize text slightly to handle newlines around prices/quantities
    clean_text = text.replace('\n', ' ')

    # 2. Split by "Sold by" to get rough item blocks
    # The first chunk is the first item's description.
    # Subsequent chunks contain the previous item's price/qty and the *next* item's description.
    chunks = re.split(r'Sold by:', text)

    if len(chunks) > 1:
        # The first chunk is just the description of the first item
        #current_desc = chunks[0].strip().split('\n')[-1] # Take the last non-empty line of the header section
        # Actually, pypdf text extraction often dumps the image text ("Arriving Wednesday") then the item name.
        # Let's try to grab the bulk of the text before "Sold by"

        # Better Strategy for B: Regex find all blocks ending in a price
        # Block structure in text stream:
        # [Item Description] ... Sold by: ... $XX.XX ... [Qty]?

        # Find all prices
        price_locs = [m for m in re.finditer(r'\$\d+\.\d{2}', text)]

        last_end = 0

        for i, p_match in enumerate(price_locs):
            # Text segment belonging to this item (roughly)
            # It starts after the previous price (or start of text) and ends at this price
            segment = text[last_end:p_match.end()]

            qty = 1

            # If this is not the first item, check the text immediately following the PREVIOUS price
            if i > 0:
                prev_end = price_locs[i-1].end()
                gap_text = text[prev_end:last_end] # Text between previous price and current item start

                # Check for a stray integer in the gap (e.g., "\n4\n")
                # We look for a digit that is on its own line
                qty_match = re.search(r'\n\s*(\d+)\s*\n', text[prev_end : prev_end+20])
                # Look immediately after previous price
                if qty_match:
                    qty = int(qty_match.group(1))

            # Determine Description
            # The description is inside 'segment', usually before "Sold by"
            # We filter out "Arriving..." or dates if they got caught up.
            desc_match = re.split(r'Sold by', segment)
            raw_desc = desc_match[0].strip()

            # Cleanup description: remove lines that are just dates or "Arriving"
            lines = raw_desc.split('\n')
            clean_lines = [l for l in lines if "Arriving" not in l and "Order" not in l and "/" not in l]
            final_desc = " ".join(clean_lines).strip()

            if final_desc:
                # One weird quirk: For the *next* item, the quantity is sitting after *current* price.
                # My logic above tries to find qty based on previous price.
                # Let's handle the extraction:

                # We need to map: Qty found AFTER previous price belongs to THIS item.
                # Exception: The FIRST item. Its quantity is usually 1 unless explicitly stated elsewhere,
                # but visually the bubble is next to the image.
                # In text stream: Item 1 Desc -> Price -> Qty 2 -> Item 2 Desc.
                # This means Qty 2 belongs to Item 2.

                # So:
                # 1. Get Qty found after previous price (defaults to 1 if none).
                # 2. Assign to current Description.

                items.append((qty, final_desc, p_match.group(), month, year))

            last_end = p_match.end()

            # Look ahead for quantity for the *next* loop (or last item check? No, logic handles it)

        return items

    return []

def parse_pack_size(description):
    """
    Attempts to extract pack size (e.g., "Pack of 10") to calculate total units.
    Returns 1 if no pack size is found.
    """
    # Pattern 3: "X Count" (common for pads/tampons) #112 count, (4 packs of 28)
    match = re.search(r'\b(\d+)\s?count', description, re.IGNORECASE)
    if match and "total" not in description:
        return int(match.group(1))

    # Pattern 1: "Pack of X" #(Pack Of 10)
    match = re.search(r'pack of (\d+)', description, re.IGNORECASE)
    if match and "count" not in description:
        return int(match.group(1))

    # Pattern 2: "X -Pack" (e.g., 3 Pack) #10 Count (Pack of 1)
    match = re.search(r'\b(\d+)\s?(-)?pack', description, re.IGNORECASE)
    if match and "count" not in description:
        return int(match.group(1))

    #50Count x 2 Packs (100 Count Total)
    match = re.search(r'\b(\d+)\s?count total', description, re.IGNORECASE)
    if match:
        return int(match.group(1))

    split_space = description.split(" ")
    if split_space[-1].isnumeric():
        return int(split_space[-1])
    #default for sports bra and no count
    if "sports bra" in description:
        return 5
    #default for underwear and no count
    if "underwear" in description:
        return 10
    return 1

def update_variables(map_var, year, month, pack_size, multiply_by, line_price) -> int:
    if line_price != "":
        price_strip = line_price.strip("$")
        prev_total = years_totals[year][month][map_var]["total_prices"]
        years_totals[year][month][map_var]["total_prices"] = round((prev_total + float(price_strip)), 2)
    prev_qty = years_totals[year][month][map_var]["quantity"]
    years_totals[year][month][map_var]["quantity"] = round( prev_qty + (int(pack_size) * int(multiply_by)))
    return int(pack_size) * int(multiply_by)

@app.route("/")
def index():
    with app.app_context():
        bra_quantities = 0
        undies_quantities = 0
        tampons_quantities = 0
        pads_quantities = 0
        dental_quantities = 0
        shower_quantities = 0
        other_quantities = 0
        for dirpath, dirnames, filenames in os.walk(os.path.abspath("receipts")):
            for file in filenames:
                full_path = os.path.join(os.path.abspath(dirpath), file)
                if os.path.isfile(full_path):
                    reader = PdfReader(full_path)
                    for page in reader.pages:

                        text = page.extract_text(0)
                        extracted = extract_items_from_text(text, file)
                        for item in extracted:
                            price_extracted = item[2]
                            mulitply_by = item[0]
                            desc = item[1]
                            month = item[3].lower()
                            year = item[4]
                            desc_lower = desc.lower()
                            if ("pads" in desc_lower or "panty liner" in desc_lower or "pantiliner" in desc_lower) and "bra" not in desc_lower:
                                pack_size = parse_pack_size(desc_lower)
                                pads_quantities += update_variables("pads", year, month, pack_size, mulitply_by, price_extracted)

                            if "tampons" in desc_lower:
                                pack_size = parse_pack_size(desc_lower)
                                tampons_quantities += update_variables("tampons", year, month, pack_size, mulitply_by, price_extracted)

                            if "underwear" in desc_lower or "panties" in desc_lower:
                                pack_size = parse_pack_size(desc_lower)
                                undies_quantities += update_variables("undies", year, month, pack_size, mulitply_by, price_extracted)

                            if "sports bra" in desc_lower or "bralette" in desc_lower:
                                pack_size = parse_pack_size(desc_lower)
                                bra_quantities += update_variables("bras", year, month, pack_size, mulitply_by, price_extracted)

                            if "toothbrush" in desc_lower or "toothpaste" in desc_lower:
                                pack_size = parse_pack_size(desc_lower)
                                dental_quantities += update_variables("dental", year, month, pack_size, mulitply_by, price_extracted)

                            if "deodorant" in desc_lower or "shower gel" in desc_lower or "shampoo" in desc_lower \
                                    or "conditioner" in desc_lower or "lotion" in desc_lower or "loofah" in desc_lower \
                                    or "soap" in desc_lower or "body wash" in desc_lower or "body spray" in desc_lower \
                                    or "exfoliating gloves" in desc_lower or "loofah" in desc_lower \
                                    or "shower cap" in desc_lower:
                                pack_size = parse_pack_size(desc_lower)
                                shower_quantities += update_variables("shower", year, month, pack_size, mulitply_by, price_extracted)

                            if "hand sanitizer" in desc_lower or "laundry detergent" in desc_lower or "hair ties" in desc_lower \
                                    or "wipes" in desc_lower or "chapstick" in desc_lower or "brush" in desc_lower \
                                    or "washcloth" in desc_lower or "towels" in desc_lower or "nail file" in desc_lower \
                                    or "nail clippers" in desc_lower or "socks" in desc_lower:
                                pack_size = parse_pack_size(desc_lower)
                                other_quantities += update_variables("other", year, month, pack_size, mulitply_by, price_extracted)

                    #    print(line)
        pads_quantities += pads_quantities + 27394
        print("total pads: ", pads_quantities)
        tampons_quantities += tampons_quantities + 81419
        print("total tampons: ", tampons_quantities)
        undies_quantities += undies_quantities + 11159
        print("total underwear: ", undies_quantities)
        bra_quantities += bra_quantities + 3942
        print("total bras: ", bra_quantities)
        print("total shower: ", shower_quantities)
        print("total dental: ", dental_quantities)
        print("total other: ", other_quantities)

        current_year = str(datetime.now().year) #"2025" #uncomment to get previous years numbers
        print("current year: ", current_year)
        if current_year == "2026":
            for key, value in order_numbers.items():
                print(key, value)
        #current_month = datetime.now().strftime("%B")
        #print("current month: ", current_month)
        ''''
        total_dental_Jan = years_totals[current_year]["january"]["dental"]["quantity"]
        total_dental_Feb = years_totals[current_year]["february"]["dental"]["quantity"]
        total_dental_March = years_totals[current_year]["march"]["dental"]["quantity"]
        total_dental_April = years_totals[current_year]["april"]["dental"]["quantity"]
        total_dental_May = years_totals[current_year]["may"]["dental"]["quantity"]
        total_dental_June = years_totals[current_year]["june"]["dental"]["quantity"]
        total_dental_July = years_totals[current_year]["july"]["dental"]["quantity"]
        total_dental_Aug = years_totals[current_year]["august"]["dental"]["quantity"]
        total_dental_Sept = years_totals[current_year]["september"]["dental"]["quantity"]
        total_dental_Oct = years_totals[current_year]["october"]["dental"]["quantity"]
        total_dental_Nov = years_totals[current_year]["november"]["dental"]["quantity"]
        total_dental_Dec = years_totals[current_year]["january"]["dental"]["quantity"]
        '''
        total_pads_year = 0
        total_tampons_year = 0
        total_bras_year = 0
        total_undies_year = 0
        total_dental_year = 0
        total_shower_year = 0
        total_other_year = 0

        prices_pads_year = 0.00
        prices_tampons_year = 0.00
        prices_bras_year = 0.00
        prices_undies_year = 0.00
        prices_dental_year = 0.00
        prices_shower_year = 0.00
        prices_other_year = 0.00
        for year, month_dict in years_totals.items():
            for month, month_item in month_dict.items():
                if int(year) == int(current_year): #"2025" #uncomment to get previous years numbers and total
                    total_pads_year += round(years_totals[year][month]["pads"]["quantity"])
                    prices_pads_year += round(years_totals[year][month]["pads"]["total_prices"], 2)
                    print("year: ", year, "month", month, "total pads", years_totals[year][month]["pads"]["quantity"], "total price", years_totals[year][month]["pads"]["total_prices"])

                    total_tampons_year += round(years_totals[year][month]["tampons"]["quantity"])
                    prices_tampons_year += round(years_totals[year][month]["tampons"]["total_prices"], 2)
                    print("year: ", year, "month", month, "total tampons", years_totals[year][month]["tampons"]["quantity"], "total price", years_totals[year][month]["tampons"]["total_prices"])

                    total_undies_year += round(years_totals[year][month]["undies"]["quantity"])
                    prices_undies_year += round(years_totals[year][month]["undies"]["total_prices"], 2)
                    print("year: ", year, "month", month, "total undies", years_totals[year][month]["undies"]["quantity"], "total price", years_totals[year][month]["undies"]["total_prices"])

                    total_bras_year += round(years_totals[year][month]["bras"]["quantity"])
                    prices_bras_year += round(years_totals[year][month]["bras"]["total_prices"], 2)
                    print("year: ", year, "month", month, "total bras", years_totals[year][month]["bras"]["quantity"], "total price", years_totals[year][month]["bras"]["total_prices"])

                    total_dental_year += round(years_totals[year][month]["dental"]["quantity"])
                    prices_dental_year += round(years_totals[year][month]["dental"]["total_prices"], 2)
                    print("year: ", year, "month", month, "total dental", years_totals[year][month]["dental"]["quantity"], "total price", years_totals[year][month]["dental"]["total_prices"])

                    total_shower_year += round(years_totals[year][month]["shower"]["quantity"])
                    prices_shower_year += round(years_totals[year][month]["shower"]["total_prices"], 2)
                    print("year: ", year, "month", month, "total shower", years_totals[year][month]["shower"]["quantity"], "total price", years_totals[year][month]["shower"]["total_prices"])

                    total_other_year += round(years_totals[year][month]["other"]["quantity"])
                    prices_other_year += round(years_totals[year][month]["other"]["total_prices"], 2)
                    print("year: ", year, "month", month, "total other", years_totals[year][month]["other"]["quantity"], "total price", years_totals[year][month]["other"]["total_prices"])

    return render_template("index.html", total_pads=pads_quantities, total_tampons=tampons_quantities,
                                   total_undies=undies_quantities, total_bras=bra_quantities,
                                    total_dental=dental_quantities, total_shower=shower_quantities,
                                    total_other=other_quantities,
                           total_pads_year=total_pads_year, prices_pads_year=round(prices_pads_year, 2),
                           total_tampons_year=total_tampons_year, prices_tampons_year=round(prices_tampons_year, 2),
                           total_bras_year=total_bras_year, prices_bras_year=round(prices_bras_year, 2),
                           total_undies_year=total_undies_year, prices_undies_year=round(prices_undies_year, 2),
                           total_shower_year=total_shower_year, prices_shower_year=round(prices_shower_year, 2),
                           total_dental_year=total_dental_year, prices_dental_year=round(prices_dental_year, 2),
                           total_other_year=total_other_year, prices_other_year=round(prices_other_year, 2),
                            total_pads_Jan = years_totals[current_year]["january"]["pads"]["quantity"],
                            total_pads_Feb = years_totals[current_year]["february"]["pads"]["quantity"],
                            total_pads_March = years_totals[current_year]["march"]["pads"]["quantity"],
                            total_pads_April = years_totals[current_year]["april"]["pads"]["quantity"],
                            total_pads_May = years_totals[current_year]["may"]["pads"]["quantity"],
                            total_pads_June = years_totals[current_year]["june"]["pads"]["quantity"],
                            total_pads_July = years_totals[current_year]["july"]["pads"]["quantity"],
                            total_pads_Aug = years_totals[current_year]["august"]["pads"]["quantity"],
                            total_pads_Sept = years_totals[current_year]["september"]["pads"]["quantity"],
                            total_pads_Oct = years_totals[current_year]["october"]["pads"]["quantity"],
                            total_pads_Nov = years_totals[current_year]["november"]["pads"]["quantity"],
                            total_pads_Dec = years_totals[current_year]["december"]["pads"]["quantity"],
                            prices_pads_Jan = years_totals[current_year]["january"]["pads"]["total_prices"],
                            prices_pads_Feb = years_totals[current_year]["february"]["pads"]["total_prices"],
                            prices_pads_March = years_totals[current_year]["march"]["pads"]["total_prices"],
                            prices_pads_April = years_totals[current_year]["april"]["pads"]["total_prices"],
                            prices_pads_May = years_totals[current_year]["may"]["pads"]["total_prices"],
                            prices_pads_June = years_totals[current_year]["june"]["pads"]["total_prices"],
                            prices_pads_July = years_totals[current_year]["july"]["pads"]["total_prices"],
                            prices_pads_Aug = years_totals[current_year]["august"]["pads"]["total_prices"],
                            prices_pads_Sept = years_totals[current_year]["september"]["pads"]["total_prices"],
                            prices_pads_Oct = years_totals[current_year]["october"]["pads"]["total_prices"],
                            prices_pads_Nov = years_totals[current_year]["november"]["pads"]["total_prices"],
                            prices_pads_Dec = years_totals[current_year]["december"]["pads"]["total_prices"],
                            total_tampons_Jan = years_totals[current_year]["january"]["tampons"]["quantity"],
                            total_tampons_Feb = years_totals[current_year]["february"]["tampons"]["quantity"],
                            total_tampons_March = years_totals[current_year]["march"]["tampons"]["quantity"],
                            total_tampons_April = years_totals[current_year]["april"]["tampons"]["quantity"],
                            total_tampons_May = years_totals[current_year]["may"]["tampons"]["quantity"],
                            total_tampons_June = years_totals[current_year]["june"]["tampons"]["quantity"],
                            total_tampons_July = years_totals[current_year]["july"]["tampons"]["quantity"],
                            total_tampons_Aug = years_totals[current_year]["august"]["tampons"]["quantity"],
                            total_tampons_Sept = years_totals[current_year]["september"]["tampons"]["quantity"],
                            total_tampons_Oct = years_totals[current_year]["october"]["tampons"]["quantity"],
                            total_tampons_Nov = years_totals[current_year]["november"]["tampons"]["quantity"],
                            total_tampons_Dec = years_totals[current_year]["december"]["tampons"]["quantity"],
                            prices_tampons_Jan = years_totals[current_year]["january"]["tampons"]["total_prices"],
                            prices_tampons_Feb = years_totals[current_year]["february"]["tampons"]["total_prices"],
                            prices_tampons_March = years_totals[current_year]["march"]["tampons"]["total_prices"],
                            prices_tampons_April = years_totals[current_year]["april"]["tampons"]["total_prices"],
                            prices_tampons_May = years_totals[current_year]["may"]["tampons"]["total_prices"],
                            prices_tampons_June = years_totals[current_year]["june"]["tampons"]["total_prices"],
                            prices_tampons_July = years_totals[current_year]["july"]["tampons"]["total_prices"],
                            prices_tampons_Aug = years_totals[current_year]["august"]["tampons"]["total_prices"],
                            prices_tampons_Sept = years_totals[current_year]["september"]["tampons"]["total_prices"],
                            prices_tampons_Oct = years_totals[current_year]["october"]["tampons"]["total_prices"],
                            prices_tampons_Nov = years_totals[current_year]["november"]["tampons"]["total_prices"],
                            prices_tampons_Dec = years_totals[current_year]["december"]["tampons"]["total_prices"],
                            total_undies_Jan = years_totals[current_year]["january"]["undies"]["quantity"],
                            total_undies_Feb = years_totals[current_year]["february"]["undies"]["quantity"],
                            total_undies_March = years_totals[current_year]["march"]["undies"]["quantity"],
                            total_undies_April = years_totals[current_year]["april"]["undies"]["quantity"],
                            total_undies_May = years_totals[current_year]["may"]["undies"]["quantity"],
                            total_undies_June = years_totals[current_year]["june"]["undies"]["quantity"],
                            total_undies_July = years_totals[current_year]["july"]["undies"]["quantity"],
                            total_undies_Aug = years_totals[current_year]["august"]["undies"]["quantity"],
                            total_undies_Sept = years_totals[current_year]["september"]["undies"]["quantity"],
                            total_undies_Oct = years_totals[current_year]["october"]["undies"]["quantity"],
                            total_undies_Nov = years_totals[current_year]["november"]["undies"]["quantity"],
                            total_undies_Dec = years_totals[current_year]["december"]["undies"]["quantity"],
                            prices_undies_Jan = years_totals[current_year]["january"]["undies"]["total_prices"],
                            prices_undies_Feb = years_totals[current_year]["february"]["undies"]["total_prices"],
                            prices_undies_March = years_totals[current_year]["march"]["undies"]["total_prices"],
                            prices_undies_April = years_totals[current_year]["april"]["undies"]["total_prices"],
                            prices_undies_May = years_totals[current_year]["may"]["undies"]["total_prices"],
                            prices_undies_June = years_totals[current_year]["june"]["undies"]["total_prices"],
                            prices_undies_July = years_totals[current_year]["july"]["undies"]["total_prices"],
                            prices_undies_Aug = years_totals[current_year]["august"]["undies"]["total_prices"],
                            prices_undies_Sept = years_totals[current_year]["september"]["undies"]["total_prices"],
                            prices_undies_Oct = years_totals[current_year]["october"]["undies"]["total_prices"],
                            prices_undies_Nov = years_totals[current_year]["november"]["undies"]["total_prices"],
                            prices_undies_Dec = years_totals[current_year]["december"]["undies"]["total_prices"],
                            total_bras_Jan = years_totals[current_year]["january"]["bras"]["quantity"],
                            total_bras_Feb = years_totals[current_year]["february"]["bras"]["quantity"],
                            total_bras_March = years_totals[current_year]["march"]["bras"]["quantity"],
                            total_bras_April = years_totals[current_year]["april"]["bras"]["quantity"],
                            total_bras_May = years_totals[current_year]["may"]["bras"]["quantity"],
                            total_bras_June = years_totals[current_year]["june"]["bras"]["quantity"],
                            total_bras_July = years_totals[current_year]["july"]["bras"]["quantity"],
                            total_bras_Aug = years_totals[current_year]["august"]["bras"]["quantity"],
                            total_bras_Sept = years_totals[current_year]["september"]["bras"]["quantity"],
                            total_bras_Oct = years_totals[current_year]["october"]["bras"]["quantity"],
                            total_bras_Nov = years_totals[current_year]["november"]["bras"]["quantity"],
                            total_bras_Dec = years_totals[current_year]["december"]["bras"]["quantity"],
                            prices_bras_Jan = years_totals[current_year]["january"]["bras"]["total_prices"],
                            prices_bras_Feb = years_totals[current_year]["february"]["bras"]["total_prices"],
                            prices_bras_March = years_totals[current_year]["march"]["bras"]["total_prices"],
                            prices_bras_April = years_totals[current_year]["april"]["bras"]["total_prices"],
                            prices_bras_May = years_totals[current_year]["may"]["bras"]["total_prices"],
                            prices_bras_June = years_totals[current_year]["june"]["bras"]["total_prices"],
                            prices_bras_July = years_totals[current_year]["july"]["bras"]["total_prices"],
                            prices_bras_Aug = years_totals[current_year]["august"]["bras"]["total_prices"],
                            prices_bras_Sept = years_totals[current_year]["september"]["bras"]["total_prices"],
                            prices_bras_Oct = years_totals[current_year]["october"]["bras"]["total_prices"],
                            prices_bras_Nov = years_totals[current_year]["november"]["bras"]["total_prices"],
                            prices_bras_Dec = years_totals[current_year]["december"]["bras"]["total_prices"],
                            total_shower_Jan = years_totals[current_year]["january"]["shower"]["quantity"],
                            total_shower_Feb = years_totals[current_year]["february"]["shower"]["quantity"],
                            total_shower_March = years_totals[current_year]["march"]["shower"]["quantity"],
                            total_shower_April = years_totals[current_year]["april"]["shower"]["quantity"],
                            total_shower_May = years_totals[current_year]["may"]["shower"]["quantity"],
                            total_shower_June = years_totals[current_year]["june"]["shower"]["quantity"],
                            total_shower_July = years_totals[current_year]["july"]["shower"]["quantity"],
                            total_shower_Aug = years_totals[current_year]["august"]["shower"]["quantity"],
                            total_shower_Sept = years_totals[current_year]["september"]["shower"]["quantity"],
                            total_shower_Oct = years_totals[current_year]["october"]["shower"]["quantity"],
                            total_shower_Nov = years_totals[current_year]["november"]["shower"]["quantity"],
                            total_shower_Dec = years_totals[current_year]["december"]["shower"]["quantity"],
                            prices_shower_Jan = years_totals[current_year]["january"]["shower"]["total_prices"],
                            prices_shower_Feb = years_totals[current_year]["february"]["shower"]["total_prices"],
                            prices_shower_March = years_totals[current_year]["march"]["shower"]["total_prices"],
                            prices_shower_April = years_totals[current_year]["april"]["shower"]["total_prices"],
                            prices_shower_May = years_totals[current_year]["may"]["shower"]["total_prices"],
                            prices_shower_June = years_totals[current_year]["june"]["shower"]["total_prices"],
                            prices_shower_July = years_totals[current_year]["july"]["shower"]["total_prices"],
                            prices_shower_Aug = years_totals[current_year]["august"]["shower"]["total_prices"],
                            prices_shower_Sept = years_totals[current_year]["september"]["shower"]["total_prices"],
                            prices_shower_Oct = years_totals[current_year]["october"]["shower"]["total_prices"],
                            prices_shower_Nov = years_totals[current_year]["november"]["shower"]["total_prices"],
                            prices_shower_Dec = years_totals[current_year]["december"]["shower"]["total_prices"],
                            total_dental_Jan = years_totals[current_year]["january"]["dental"]["quantity"],
                            total_dental_Feb = years_totals[current_year]["february"]["dental"]["quantity"],
                            total_dental_March = years_totals[current_year]["march"]["dental"]["quantity"],
                            total_dental_April = years_totals[current_year]["april"]["dental"]["quantity"],
                            total_dental_May = years_totals[current_year]["may"]["dental"]["quantity"],
                            total_dental_June = years_totals[current_year]["june"]["dental"]["quantity"],
                            total_dental_July = years_totals[current_year]["july"]["dental"]["quantity"],
                            total_dental_Aug = years_totals[current_year]["august"]["dental"]["quantity"],
                            total_dental_Sept = years_totals[current_year]["september"]["dental"]["quantity"],
                            total_dental_Oct = years_totals[current_year]["october"]["dental"]["quantity"],
                            total_dental_Nov = years_totals[current_year]["november"]["dental"]["quantity"],
                            total_dental_Dec = years_totals[current_year]["december"]["dental"]["quantity"],
                            prices_dental_Jan = years_totals[current_year]["january"]["dental"]["total_prices"],
                            prices_dental_Feb = years_totals[current_year]["february"]["dental"]["total_prices"],
                            prices_dental_March = years_totals[current_year]["march"]["dental"]["total_prices"],
                            prices_dental_April = years_totals[current_year]["april"]["dental"]["total_prices"],
                            prices_dental_May = years_totals[current_year]["may"]["dental"]["total_prices"],
                            prices_dental_June = years_totals[current_year]["june"]["dental"]["total_prices"],
                            prices_dental_July = years_totals[current_year]["july"]["dental"]["total_prices"],
                            prices_dental_Aug = years_totals[current_year]["august"]["dental"]["total_prices"],
                            prices_dental_Sept = years_totals[current_year]["september"]["dental"]["total_prices"],
                            prices_dental_Oct = years_totals[current_year]["october"]["dental"]["total_prices"],
                            prices_dental_Nov = years_totals[current_year]["november"]["dental"]["total_prices"],
                            prices_dental_Dec = years_totals[current_year]["december"]["dental"]["total_prices"],
                            total_other_Jan = years_totals[current_year]["january"]["other"]["quantity"],
                            total_other_Feb = years_totals[current_year]["february"]["other"]["quantity"],
                            total_other_March = years_totals[current_year]["march"]["other"]["quantity"],
                            total_other_April = years_totals[current_year]["april"]["other"]["quantity"],
                            total_other_May = years_totals[current_year]["may"]["other"]["quantity"],
                            total_other_June = years_totals[current_year]["june"]["other"]["quantity"],
                            total_other_July = years_totals[current_year]["july"]["other"]["quantity"],
                            total_other_Aug = years_totals[current_year]["august"]["other"]["quantity"],
                            total_other_Sept = years_totals[current_year]["september"]["other"]["quantity"],
                            total_other_Oct = years_totals[current_year]["october"]["other"]["quantity"],
                            total_other_Nov = years_totals[current_year]["november"]["other"]["quantity"],
                            total_other_Dec = years_totals[current_year]["december"]["other"]["quantity"],
                            prices_other_Jan = years_totals[current_year]["january"]["other"]["total_prices"],
                            prices_other_Feb = years_totals[current_year]["february"]["other"]["total_prices"],
                            prices_other_March = years_totals[current_year]["march"]["other"]["total_prices"],
                            prices_other_April = years_totals[current_year]["april"]["other"]["total_prices"],
                            prices_other_May = years_totals[current_year]["may"]["other"]["total_prices"],
                            prices_other_June = years_totals[current_year]["june"]["other"]["total_prices"],
                            prices_other_July = years_totals[current_year]["july"]["other"]["total_prices"],
                            prices_other_Aug = years_totals[current_year]["august"]["other"]["total_prices"],
                            prices_other_Sept = years_totals[current_year]["september"]["other"]["total_prices"],
                            prices_other_Oct = years_totals[current_year]["october"]["other"]["total_prices"],
                            prices_other_Nov = years_totals[current_year]["november"]["other"]["total_prices"],
                            prices_other_Dec = years_totals[current_year]["december"]["other"]["total_prices"])



if __name__ == '__main__':
    app.run(debug=True)