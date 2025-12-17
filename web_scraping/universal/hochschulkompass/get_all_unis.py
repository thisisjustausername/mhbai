# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: scrape all universities from Hochschulkompass hochschulkompass.de; implemented in Un-sc-0003
# Status: PROTOTYPING
# FileID: Un-sc-0002

import json
import requests

def get_unis() -> list[dict[str, str]]:
    """
    Fetches the list of universities from the Hochschulkompass TXT download endpoint.

    Returns:
        list[dict[str, str]]: A list of dictionaries containing data for each university in Germany.
    """

    # initialize URL for the Hochschulkompass TXT download
    url = "https://hs-kompass.de/kompass/xml/download/hs_liste.txt"

    # make the GET request to fetch the data
    response = requests.get(url)
    response.raise_for_status()

    # extract the data
    data = response.text
    
    # clean the data
    data = data.split("\n")
    header = data[0].split("\t")
    universities = [line.split("\t") for line in data[1:] if line]

    rename_dict = {"Hs-Nr.": "hs_nr",                                   # used
                   "Hochschulkurzname": "short_name",                   # unused
                   "Hochschulname": "name",                             # used
                   "Adressname der Hochschule": "address_name",         # unused
                   "Hochschultyp": "type",                              # unknown
                   "Trägerschaft": "holder_type",                       # unknown
                   "Bundesland": "state",                               # unused
                   "Anzahl Studierende": "students",                    # unused
                   "Gründungsjahr": "founded",                          # unused
                   "Promotionsrecht": "doctoral_rights",                # unused
                   "Habilationsrecht": "habilitation_rights",           # unused
                   "Straße": "street",                                  # unused
                   "Postleitzahl (Hausanschrift)": "postal_code",       # unused
                   "Ort": "city",                                       # unused
                   "Telefonvorwahl": "phone_area_code",                 # unused
                   "Telefon": "phone_number",                           # unused
                   "Fax": "fax_number",                                 # unused
                   "Home Page": "website",                              # used
                   "Mitglied HRK": "hrk_member"                         # used
                   }

    clean_data = [{h: u for h, u in zip(header, uni)} for uni in universities]

    return clean_data

def save_info_to_db(cursor, uni_info: dict[str, str]) -> None:
    """
    Saves the university information to the database.

    Args:
        cursor: Database cursor to execute the SQL commands.
        uni_info (dict[str, str]): A dictionary containing university information.
    """
    
    """result = db.select(
        cursor=cursor,
        table="all_unis.universities",
        keywords={"name", "city", "source"}, 
    )"""
    pass

if __name__ == "__main__":
    result = get_unis()
    print(json.dumps(result, indent=4))