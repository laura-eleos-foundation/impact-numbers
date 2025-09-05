import os
from pypdf import PdfReader
from flask import Flask, render_template
import re

file_names = []

app = Flask(__name__)

@app.route("/")
def index():
    with app.app_context():
        bra_quantities = 0
        undies_quantities = 0
        tampons_quantities = 0
        pads_quantities = 0
        for entry in os.listdir(os.path.abspath("receipts")):
            full_path = os.path.join(os.path.abspath("receipts"), entry)
            if os.path.isfile(full_path):
                file_names.append(entry)

                reader = PdfReader(full_path)
                for page in reader.pages:
                    text = page.extract_text(0)
                    lines = text.split("\n")
                    prevLine = None
                    for line in lines:
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
                                    #splitSpace = desc.split(" ")
                                    #num_pads = int(splitSpace[1])
                            if prevLine is not None and prevLine.isdecimal():
                                int_prevLine = int(prevLine)
                                pads_quantities += num_pads * int_prevLine
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
                            else:
                                tampons_quantities += num_tamps
                        if "Underwear" in line or "underwear" in line or "panties" in line or "Panties" in line:
                            splitComma = line.split(",")
                            num_panties = 0
                            for desc in splitComma:
                                pattern = "-Pack"
                                match_obj = re.search(pattern, desc)
                                if "Pack of" in desc and "Count" not in desc:
                                    splitSpace = desc.split(" ")
                                    num_panties = int(splitSpace[2])
                                elif "Pack-" in desc:
                                    splitSpace = desc.split(" ")
                                    removeWord = splitSpace[1].removesuffix("-Pack").removeprefix("Hipster-")
                                    num_panties = int(removeWord)
                                elif "-pack" in desc:
                                    splitSpace = desc.split(" ")
                                    removeWord = splitSpace[2].removesuffix("-pack").removeprefix("Hipster-")
                                    num_panties = int(removeWord)
                                elif match_obj:
                                    splitSpace = desc.split(" ")
                                    removeWord = splitSpace[1].removesuffix("-Pack").removeprefix("Hipster-")
                                    num_panties = int(removeWord)
                                elif "Pack " in desc or "pack" in desc:
                                    splitSpace = desc.split(" ")
                                    if splitSpace[0].isdecimal():
                                        num_panties = int(splitSpace[0])
                                elif "Pack" not in desc and "Fruit of the Loom" in desc:
                                    num_panties = 12
                            if prevLine is not None and isinstance(prevLine, int):
                                int_prevLine = int(prevLine)
                                undies_quantities += num_panties * int_prevLine
                            else:
                                undies_quantities += num_panties
                        if "Racerback Sports Bras" in line and "MIRITY Women" in line and "Pack" not in line:
                            if prevLine is not None and isinstance(prevLine, int):
                                int_prevLine = int(prevLine)
                                bra_quantities += 5 * int_prevLine
                            else:
                                bra_quantities += 5
                        elif "Racerback Sports Bra" in line and "MIRITY Women" not in line:
                            if prevLine is not None and isinstance(prevLine, int):
                                int_prevLine = int(prevLine)
                                bra_quantities += 3 * int_prevLine
                            else:
                                bra_quantities += 3
                        prevLine = line
                        #print(line)

        print("total pads: ", pads_quantities)
        print("total tampons: ", tampons_quantities)
        print("total underwear: ", undies_quantities)
        print("total bras: ", bra_quantities)
        #print(file_names)
    return render_template("index.html", total_pads=pads_quantities, total_tampons=tampons_quantities,
                                   total_undies=undies_quantities, total_bras=bra_quantities)



if __name__ == '__main__':
    app.run(debug=True)