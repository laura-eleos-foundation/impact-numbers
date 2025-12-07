import os
from pypdf import PdfReader
from flask import Flask, render_template
import re
from datetime import datetime

file_names = []
years_totals = {
    "2025":
        {"January": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "February": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "March": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "April": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "May": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "June": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "July": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "August": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "September": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "October": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "November": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
         "December": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0}},
    "2024":         {"January": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "February": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "March": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "April": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "May": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "June": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "July": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "August": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "September": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "October": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "November": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "December": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0}},
    "2023":         {"January": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "February": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "March": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "April": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "May": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "June": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "July": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "August": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "September": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "October": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "November": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "December": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0}},
    "2022":         {"January": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "February": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "March": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "April": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "May": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "June": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "July": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "August": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "September": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "October": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "November": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "December": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0}},
    "2021":         {"January": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "February": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "March": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "April": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "May": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "June": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "July": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "August": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "September": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "October": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "November": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0},
                     "December": {"pads": 0, "tampons": 0, "undies": 0, "bras": 0}}
}

app = Flask(__name__)

@app.route("/")
def index():
    with app.app_context():
        bra_quantities = 0
        undies_quantities = 0
        tampons_quantities = 0
        pads_quantities = 0
        for dirpath, dirnames, filenames in os.walk(os.path.abspath("receipts")):
            for file in filenames:
                full_path = os.path.join(os.path.abspath(dirpath), file)
                if os.path.isfile(full_path):
                    #print("full path: ", full_path)
                    file_names.append(file)
                    month = ""
                    year = ""
                    reader = PdfReader(full_path)
                    for page in reader.pages:

                        text = page.extract_text(0)
                        lines = text.split("\n")
                        prevLine = None
                        for line in lines:

                            if "Order placed" in line or "Order Placed:" in line:
                                splitSpace= line.split(" ")
                                month = splitSpace[2]
                                year = splitSpace[4]
                                #print("month: ", month)
                                #print("year: ", year)

                            if "Pads" in line or "pads" in line:
                                splitComma = line.split(",")
                                num_pads = 0
                                for desc in splitComma:
                                    pattern = "Count"
                                    match_obj = re.search(pattern, desc)
                                    if match_obj:
                                        splitSpace = desc.split(" ")
                                        if splitSpace[0].isnumeric():
                                            num_pads = int(splitSpace[0])
                                        elif splitSpace[1].isnumeric():
                                            num_pads = int(splitSpace[1])
                                        else:
                                            removeWord = splitSpace[1].removesuffix("Count")
                                            num_pads = int(removeWord)
                                if prevLine is not None and prevLine.isdecimal():
                                    int_prevLine = int(prevLine)
                                    pads_quantities += num_pads * int_prevLine
                                    years_totals[year][month]["pads"] += num_pads * int_prevLine
                            if "Tampons" in line or "tampons" in line:
                                splitComma = line.split(",")
                                num_tamps = 0
                                for desc in splitComma:
                                    pattern = "Count"
                                    match_obj = re.search(pattern, desc)
                                    if match_obj:
                                        splitSpace = desc.split(" ")
                                        if splitSpace[0].isnumeric():
                                            num_tamps = int(splitSpace[0])
                                        elif splitSpace[1].isnumeric():
                                            num_tamps = int(splitSpace[1])
                                        else:
                                            removeWord = splitSpace[1].removesuffix("Count")
                                            num_tamps = int(removeWord)
                                if prevLine is not None and prevLine.isdecimal():
                                    int_prevLine = int(prevLine)
                                    tampons_quantities += num_tamps * int_prevLine
                                    years_totals[year][month]["tampons"] += num_tamps * int_prevLine
                                else:
                                    tampons_quantities += num_tamps
                                    years_totals[year][month]["tampons"] += num_tamps
                            if "Underwear" in line or "underwear" in line or "panties" in line or "Panties" in line:
                                splitComma = line.split(",")
                                num_panties = 0
                                for desc in splitComma:
                                    pattern = "-Pack"
                                    match_obj = re.search(pattern, desc)
                                    #10 Count (Pack of 1)
                                    if "Pack of" in desc and "Count" in desc:
                                        splitSpace = desc.split(" ")
                                        if splitSpace[0].isdecimal():
                                            num_panties = int(splitSpace[0])
                                    #Pack of 6
                                    if "Pack of" in desc and "Count" not in desc and "(" not in desc:
                                        splitSpace = desc.split(" ")
                                        if splitSpace[0].isdecimal():
                                            num_panties = int(splitSpace[2])
                                    #(Pack of 12)
                                    if "(Pack of" in desc and "Count" not in desc:
                                        splitSpace = desc.split(" ")
                                        if splitSpace[0].isdecimal():
                                            num_panties = int(splitSpace[2].removesuffix(")"))
                                    #Low Rise Brief-10 Pack-Purple/Blue/White,
                                    elif "Pack-" in desc and "Low Rise" in desc:
                                        splitSpace = desc.split(" ")
                                        removeWord = splitSpace[3].removesuffix("-Pack").removeprefix("Hipster-").removeprefix("Brief-").removeprefix("Blend-")
                                        num_panties = int(removeWord)
                                    #Brief-20 Pack-Black/Pink/Grey
                                    elif "Pack-" in desc:
                                        splitSpace = desc.split(" ")
                                        removeWord = splitSpace[1].removesuffix("-Pack").removeprefix("Hipster-").removeprefix("Brief-").removeprefix("Blend-")
                                        num_panties = int(removeWord)
                                    #Value 10-pack
                                    elif "-pack" in desc and "Value " in desc:
                                        splitSpace = desc.split(" ")
                                        removeWord = splitSpace[2].removesuffix("-pack").removeprefix("Hipster-").removeprefix("Blend-")
                                        num_panties = int(removeWord)
                                    #10-pack Assorted
                                    elif "-pack" in desc and "Assorted" in desc:
                                        splitSpace = desc.split(" ")
                                        removeWord = splitSpace[1].removesuffix("-").removesuffix("-pack").removesuffix(" ").removeprefix("Hipster-").removeprefix("Blend-")
                                        num_panties = int(removeWord)
                                    #Value, 10-pack
                                    elif "-pack" in desc and "Value " not in desc and "Assorted" not in desc:
                                        #splitSpace = desc.split(" ")
                                        removeWord = desc.removesuffix("-").removesuffix("-pack").removesuffix(" ").removeprefix("Hipster-").removeprefix("Blend-")
                                        num_panties = int(removeWord)
                                    #12-Pack
                                    elif match_obj:
                                        splitSpace = desc.split(" ")
                                        if splitSpace[0].isdecimal():
                                            removeWord = splitSpace[0].removesuffix("-Pack").removeprefix("Hipster-")
                                            num_panties = int(removeWord)
                                        #if splitSpace[1].isdecimal():
                                         #   removeWord = splitSpace[1].removesuffix("-Pack").removeprefix("Hipster-")
                                          #  num_panties = int(removeWord)
                                    #10 Pack - Hi Cut Assorted 1
                                    #Brief - 12 Pack Assorted Colors
                                    elif "Pack " in desc or "pack" in desc:
                                        splitSpace = desc.split(" ")
                                        if splitSpace[0].isdecimal():
                                            num_panties = int(splitSpace[0])
                                        elif splitSpace[1].isdecimal():
                                            num_panties = int(splitSpace[1])
                                        elif splitSpace[2].isdecimal():
                                            num_panties = int(splitSpace[2])
                                    elif "Pack" not in desc and "Fruit of the Loom" in desc:
                                        num_panties = 12
                                if prevLine is not None and isinstance(prevLine, int):
                                    int_prevLine = int(prevLine)
                                    undies_quantities += num_panties * int_prevLine
                                    years_totals[year][month]["undies"] += num_panties * int_prevLine
                                else:
                                    undies_quantities += num_panties
                                    years_totals[year][month]["undies"] += num_panties
                            if "Racerback Sports Bras" in line and "MIRITY Women" in line and "Pack" not in line:
                                if prevLine is not None and isinstance(prevLine, int):
                                    int_prevLine = int(prevLine)
                                    bra_quantities += 5 * int_prevLine
                                    years_totals[year][month]["bras"] += 5 * int_prevLine
                                else:
                                    bra_quantities += 5
                                    years_totals[year][month]["bras"] += 5
                            elif "Racerback Sports Bra" in line and "MIRITY Women" not in line:
                                if prevLine is not None and isinstance(prevLine, int):
                                    int_prevLine = int(prevLine)
                                    bra_quantities += 3 * int_prevLine
                                    years_totals[year][month]["bras"] += 3 * int_prevLine
                                else:
                                    bra_quantities += 3
                                    years_totals[year][month]["bras"] += 3
                            elif "Bra" in line or "bra" in line:
                                if prevLine is not None and isinstance(prevLine, int):
                                    int_prevLine = int(prevLine)
                                    bra_quantities += int_prevLine
                            prevLine = line
                    #    print(line)

        print("total pads: ", pads_quantities)
        print("total tampons: ", tampons_quantities)
        print("total underwear: ", undies_quantities)
        print("total bras: ", bra_quantities)
        current_year = datetime.now().year
        print("current year: ", current_year)
        current_month = datetime.now().strftime("%B")
        print("current month: ", current_month)
        total_pads_year = 0
        total_pads_Jan = 0
        total_pads_Feb = 0
        total_pads_March = 0
        total_pads_April = 0
        total_pads_May = 0
        total_pads_June = 0
        total_pads_July = 0
        total_pads_Aug = 0
        total_pads_Sept = 0
        total_pads_Oct = 0
        total_pads_Nov = 0
        total_pads_Dec =0

        total_tampons_year = 0
        total_bras_year = 0
        total_undies_year = 0
        for year, month_dict in years_totals.items():
            for month, month_item in month_dict.items():
                if int(year) == int(current_year):
                    total_pads_year += years_totals[year][month]["pads"]
                    print("year: ", year, "month", month, "total pads", years_totals[year][month]["pads"])
                    total_tampons_year += years_totals[year][month]["tampons"]
                    print("year: ", year, "month", month, "total tampons", years_totals[year][month]["tampons"])
                    total_undies_year += years_totals[year][month]["undies"]
                    print("year: ", year, "month", month, "total undies", years_totals[year][month]["undies"])
                    total_bras_year += years_totals[year][month]["bras"]
                    print("year: ", year, "month", month, "total bras", years_totals[year][month]["bras"])
    return render_template("index.html", total_pads=pads_quantities, total_tampons=tampons_quantities,
                                   total_undies=undies_quantities, total_bras=bra_quantities,
                           total_pads_year=total_pads_year, total_tampons_year=total_tampons_year,
                           total_bras_year=total_bras_year, total_undies_year=total_undies_year)



if __name__ == '__main__':
    app.run(debug=True)