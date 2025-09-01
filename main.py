import os
from pypdf import PdfReader
from flask import Flask, render_template

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
                                if "Count" in desc:
                                    splitSpace = desc.split(" ")
                                    num_pads = int(splitSpace[1])
                                    print("count for pad found", splitSpace[1])
                            if prevLine is not None:
                                int_prevLine = int(prevLine)
                                pads_quantities += num_pads * int_prevLine
                                #print("to multiply by: ", prevLine)
                        if "Tampons" in line or "tampons" in line:
                            splitComma = line.split(",")
                            num_tamps = 0
                            for desc in splitComma:
                                if "Count" in desc:
                                    splitSpace = desc.split(" ")
                                    num_tamps = int(splitSpace[1])
                                    print("count for tampons found", splitSpace[1])
                            if prevLine is not None:
                                int_prevLine = int(prevLine)
                                tampons_quantities += num_tamps * int_prevLine
                                #print("to multiply by: ", prevLine)
                        if "Underwear" in line or "underwear" in line:
                            splitComma = line.split(",")
                            num_panties = 0
                            for desc in splitComma:
                                if "Pack of" in desc or "pack of" in desc:
                                    splitSpace = desc.split(" ")
                                    num_panties = int(splitSpace[2])
                                    print("count for underwear found", num_panties)
                            if prevLine is not None and isinstance(prevLine, int):
                                int_prevLine = int(prevLine)
                                undies_quantities += num_panties * int_prevLine
                                #print("to multiply by: ", prevLine)
                            else:
                                undies_quantities += num_panties
                        if "Racerback Sports Bras" in line:
                            bra_quantities += 3
                        prevLine = line

        print("total pads: ", pads_quantities)
        print("total tampons: ", tampons_quantities)
        print("total underwear: ", undies_quantities)
        print("total bras: ", bra_quantities)
        print(file_names)
    return render_template("index.html", total_pads=pads_quantities, total_tampons=tampons_quantities,
                                   total_undies=undies_quantities, total_bras=bra_quantities)



if __name__ == '__main__':
    app.run(debug=True)