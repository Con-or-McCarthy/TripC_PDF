import argparse

from download_overzicht import download_main
from edit_pdf import edit_main


if __name__ == "__main__":
    # Accept arguments to specify desired factuur
    parser = argparse.ArgumentParser()
    parser.add_argument("-month", type=str, help="Month to download", default=None)
    parser.add_argument("-year", type=str, help="Corresponding year of month", default="2024")
    parser.add_argument("-extra_stops", type=list, help="Additional stops frmo this month which should be added to totals", default=[])
    args = parser.parse_args()
    month = args.month
    year = args.year
    extra_stops = args.extra_stops
    if month:
        MONTH = month + " " + year
        print("searching for", MONTH)
    else:
        MONTH = None

    # download pdf
    raw_file_path = download_main(desired_month=MONTH)
    # edit pdf + calculate total
    edit_main(raw_file_path, add_stops=extra_stops)