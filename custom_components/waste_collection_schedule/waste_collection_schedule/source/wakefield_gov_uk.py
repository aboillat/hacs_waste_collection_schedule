from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Wakefield Council"
DESCRIPTION = "Source for Wakefield.gov.uk services for Wakefield Council"
URL = "https://wakefield.gov.uk"

TEST_CASES = {
    "uprn1": {"uprn": "63024087"},
    "uprn2": {"uprn": 63105305},
    "uprn3": {"uprn": "63012193"},
}

TYPES = {
    "Household": {"icon": "mdi:trash-can", "alias": "Household"},
    "Mixed": {"icon": "mdi:recycle", "alias": "Mixed Recycling"},
    "Garden": {"icon": "mdi:leaf", "alias": "Garden"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your UPRN (available from [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)). "
          "Alternatively: you can also see it in the URL/location bar of your browser when you search the Wakefield site manually, look for 'uprn=' in the url and take the numbers immediately after."
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self) -> List[Collection]:
        entries = []
        with requests.Session() as sess:
            url = "https://www.wakefield.gov.uk/where-i-live/"
            # Removed the extra curly braces around self._uprn which would create a set string
            request = sess.get(url, params={"uprn": self._uprn, "a": "Your Address"})
            soup = BeautifulSoup(request.content, "html.parser")
            
            collection_sections = soup.select(".tablet\\:l-col-fb-4.u-mt-10")
            
            for section in collection_sections:
                # Use a set to automatically filter out duplicate dates for THIS bin type
                collection_dates = set()
                bin_type_raw = section.find("strong").text.split(" ")[0]
                bin_type = TYPES.get(bin_type_raw)
                
                if not bin_type:
                    continue

                # 1. Grab dates from the 'u-mb-2' divs (usually Prev/Next)
                date_elements = section.select(".u-mb-2")
                # 2. Grab dates from 'li' elements (future dates)
                date_elements.extend(section.find_all("li"))

                for element in date_elements:
                    if ", " not in element.text:
                        continue
                    try:
                        # Parsing date from format "Monday, 14 April 2026"
                        date_str = element.text.split(", ")[1].strip()
                        clean_date = datetime.strptime(date_str, "%d %B %Y").date()
                        collection_dates.add(clean_date)
                    except (ValueError, IndexError):
                        continue

                # Add the unique dates for this category to the final entries
                for collection_date in collection_dates:
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=bin_type["alias"],
                            icon=bin_type["icon"],
                        )
                    )
                    
        return entries
