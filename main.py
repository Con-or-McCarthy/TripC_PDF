import argparse

from download_overzicht import download_main
from edit_pdf import edit_main


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-month", type=str, help="Month to download", default=None)
    args = parser.parse_args()
    MONTH = args.month

    # download pdf
    raw_file_path = download_main(desired_month=MONTH)
    # edit pdf + calculate total
    edit_main(raw_file_path)