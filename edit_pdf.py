import re
import os
import random
import PyPDF2
import fitz
from fpdf import FPDF

DECLARATIONS_DIR = os.getcwd() + '/declarations/'
# Stops which if found, indicate the NFI was visited that day
STOPS_OF_INTEREST = ["Den Haag Centraal", "Den Haag HS", "Den Haag Ypenburg", "Laan van Ypenburg", "Noordwijkerhout, Langelaan"]
# Specific personal info which I do not want to be redacted
UNREDACTED_INFO = ["C.M.C. Mccarthy", "Factuurnummer"]

# BUG: This script does not work for OV-fiets. It leaves the info but redacts the charge and does not add it - can investigate using Augustus 2023

# find the dates on which the NFI was visited
def find_dates(path_to_pdf):
    NFI_dates = []
    # Initialize a PDF reader object
    with open(path_to_pdf, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Loop through each page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            
            # Extract text from the page
            text = page.extract_text()
            
            # Split the text into lines
            lines = text.split("\n")
            
            # Loop through each line
            for line in lines:
                for stop in STOPS_OF_INTEREST:
                    # Check if the line contains "Den Haag Centraal"
                    if stop in line:
                        # Use regular expression to extract the date
                        match = re.search(r"\d{2}-\d{2}-\d{4}", line)
                        if match:
                            date = match.group(0)
                            NFI_dates.append(date)

    return list(set(NFI_dates))


# Calculate daily charge also then write to file
def calculate_charge(path_to_pdf, date_list):
    daily_charges = {}
    with open(path_to_pdf, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Loop through each page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            
            # Extract text from the page
            text = page.extract_text()
            
            # Split the text into lines
            lines = text.split("\n")
            
            # Loop through each line
            for line in lines:
                # Loop through dates
                for date in date_list:
                    # Check if the line contains "Den Haag Centraal"
                    if date in line:
                        # Use regular expression to extract the date
                        match = re.search(r"\d{1,2},\d{2}", line)
                        # Extract the charge for that 
                        if match:
                            charge = match.group(0)
                            charge = float(charge.replace(",","."))

                            # Add the charge to the date
                            if date not in daily_charges:
                                daily_charges[date] = charge
                            else: 
                                daily_charges[date] += charge
    
    # Round charges to nearest cent
    total_charge = round(sum(daily_charges.values()), 2)
    daily_charges = {k: round(v, 2) for k, v in daily_charges.items()}
    return daily_charges, total_charge


class Redactor: 
    # constructor
    def __init__(self, read_path, write_path):
        self.read_path = read_path
        self.write_path = write_path
 
    def redaction(self, NFI_dates):
        # opening the pdf
        doc = fitz.open(self.read_path)
        noredact_pattern = '|'.join(re.escape(s) for s in UNREDACTED_INFO)
         
        # iterating through pages
        for page in doc:
           
            # _wrapContents is needed for fixing
            # alignment issues with rect boxes in some
            # cases where there is alignment issue
            page.wrap_contents()

            text_page = page.get_textpage()
            # Extract text as a list of text lines grouped by block
            text_lines = text_page.extractBLOCKS()

            for line in text_lines:
                # Skip/don't redact if not-to-be-redacted info is present
                if bool(re.search(noredact_pattern, line[4])):
                    continue
                # Skip/don't redact if it's an NFI date
                elif line[4][:10] in NFI_dates:
                    continue
                # Otherwise, redact
                else:
                    # Create bounding box for the entire line
                    line_bbox = fitz.Rect(line[0], line[1], line[2], line[3])
                    # Create a redaction annotation for the entire line
                    page.add_redact_annot(line_bbox, fill=(0, 0, 0))
            

            # applying the redaction
            page.apply_redactions()
             
        # saving it to a new pdf
        doc.save(self.write_path)
        print(f"Document saved to: {self.write_path}")


# Given location of unredacted pdf, get location for writing new pdf
def get_PDF_names(path_to_pdf, total_charge):
    total_charge = str(total_charge).replace(".","_")
    
    # Split the original path into directory and filename
    directory, filename = os.path.split(path_to_pdf)
    # Split the filename into name and extension
    name, extension = os.path.splitext(filename)
    # Extract variable part
    year, month = name.split('_')[0:2]

    # create new name 
    new_name = f"redacted_{year}_{month}_{total_charge}{extension}"
    # create new path
    new_path = os.path.join(directory, new_name)
    
    return new_path 

def save_charges(write_path, daily_charges, total_charge):
    # get name of file
    name, extension = os.path.splitext(write_path)
    # Create a file
    with open(f"{name}.txt", 'w') as f:  
        # Write daily charges to file
        f.write("Daily Charges:\n")
        for key, value in daily_charges.items():  
            f.write('%s: %s\n' % (key, value))
        # Write Total Charge to file
        f.write(f"Total Charge: {total_charge}")

    # Make pdf
    pdf = FPDF()   
    pdf.add_page()
    pdf.set_font("Arial", size = 15)
    f = open(f"{name}.txt", "r")
    for x in f:
        # # Randomly set text colour
        # r,g,b = random.sample(range(0, 255), 3)
        # pdf.set_text_color(r,g,b)
        pdf.cell(200, 10, txt = x, ln = 1, align = 'C')
    # save the pdf with name .pdf
    pdf.output(f"{name}_totals.pdf")   

    # Delete .txt file
    os.unlink(f"{name}.txt")

    print(f"Saved daily charges to {name}_totals.pdf")


def edit_main(read_path=DECLARATIONS_DIR+"1111_december_overzicht.pdf"):

    # Find dates of NFI visits
    NFI_dates = find_dates(read_path)
    print("Dates of NFI visits:", NFI_dates)

    # Calculate money owed
    daily_charges, total_charge = calculate_charge(read_path, NFI_dates)
    print("Daily charges for the month:", daily_charges)
    print("Total Charges for the month:", total_charge)


    # Get paths of where to read pdf from and what to name new pdf
    write_path = get_PDF_names(read_path, total_charge)

    # Save charges to .pdf file
    save_charges(write_path, daily_charges, total_charge)

    # Redact unnecessary lines
    redactor = Redactor(read_path, write_path)
    redactor.redaction(NFI_dates)
    print("Redaction complete")

if __name__ =="__main__":
    edit_main(read_path=DECLARATIONS_DIR+"2023_december_overzicht.pdf")


