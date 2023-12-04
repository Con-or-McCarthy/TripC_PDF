import re
import os
import PyPDF2
import fitz

DECLARATIONS_DIR = os.getcwd() + '/declarations/'
# Stops which if found, indicate the NFI was visited that day
STOPS_OF_INTEREST = ["Den Haag Centraal", "Den Haag HS", "Den Haag Ypenburg", "Laan van Ypenburg", "Noordwijkerhout, Langelaan"]

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


def calculate_charge(path_to_pdf, date_list):
    total_charge = 0
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
                        if match:
                            charge = match.group(0)
                            charge = float(charge.replace(",","."))
                            total_charge += charge
    return total_charge


class Redactor: 
    # constructor
    def __init__(self, read_path, write_path):
        self.read_path = read_path
        self.write_path = write_path
 
    def redaction(self, NFI_dates):
        # opening the pdf
        doc = fitz.open(self.read_path)
         
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
                # Skip/don't redact if it's an NFI date
                if line[4][:10] in NFI_dates:
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


def edit_main(read_path=DECLARATIONS_DIR+"1111_december_overzicht.pdf"):

    # Find dates of NFI visits
    NFI_dates = find_dates(read_path)
    print("Dates of NFI visits:", NFI_dates)

    # Calculate money owed
    total_charge = calculate_charge(read_path, NFI_dates)
    total_charge = round(total_charge, 2)
    print("Total charge for month:", total_charge)

    # Get paths of where to read pdf from and what to name new pdf
    write_path = get_PDF_names(read_path, total_charge)

    # Redact unnecessary lines
    redactor = Redactor(read_path, write_path)
    redactor.redaction(NFI_dates)
    print("Redaction complete")

if __name__ =="__main__":
    edit_main()


