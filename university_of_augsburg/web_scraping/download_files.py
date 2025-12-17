# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: download mhbs from University of Augsburg
# Status: VERSION 1.0
# FileID: Au-sc-0001


import math
import psycopg2
import requests
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

from database import database as db


def fetch_valid_urls(url_list=["https://mhb.uni-augsburg.de/"], final_links=[]) -> list[str]:
    """
    searches for all mhb links and saves them as valid urls

    Args:
        url_list (list): list of urls to search for mhb links
        final_links (list): list of valid mhb links found so far
    Returns:
        list[str] | function: list of all valid mhb links or recursively calls itself to search for more links
    """

    # list of newly found urls in this iteration
    new_urls: list[str] = []

    # iterate through all urls in url_list
    for link in url_list:

        # fetch content of the url
        try:
            result = requests.get(link)
        except Exception as e:
            print(f"Error fetching {link}: {e}")
            continue
        # check for errors
        if result.status_code != 200:
            raise Exception("Error fetching mhb links")

        # parse the content using BeautifulSoup
        soup = BeautifulSoup(result.text, 'lxml')

        # find container containing all folder or mhb urls
        link_container = soup.find("div", class_="section-inner mt-0 mb-0")

        # this line is optional since it is a direct child of link_container with the full content
        link_container = link_container.find("div", class_="textEditorContent")

        # find all urls in the container
        list_items = link_container.find_all('li')
        links = [i.find('a')['href'] for i in list_items]
        links = [link + i for i in links]

        # iterate from the end in order to not change the next indices when popping an element from the list
        for curr_link in links:
            # if file is a pdf, add it to final_links, else add it to new_urls to search for more links
            if curr_link.endswith(".pdf"):
                final_links.append(curr_link)
            else:
                new_urls.append(curr_link)
    
    # if no new urls were found, return the final list of valid mhb links
    if len(new_urls) == 0:
        return final_links
    
    # call the function recursively with the new urls found
    return fetch_valid_urls(new_urls, final_links)


def fetch_pdf(cursor: db.cursor, web_url: str, adapt_file_names: bool = False) -> tuple[str, bytes]:
    """
    fetches the pdf from the given web url

    Args:
        cursor (db.cursor): database cursor
        web_url (str): url of the pdf to fetch
        adapt_file_names (bool): whether to adapt file names in order to reduce conflicts
    Returns:
        tuple[str, bytes]: file name and content of the pdf
    """

    # fetch file
    pdf = requests.get(web_url)

    file_name = ""

    # adapt file name if specified
    if adapt_file_names is True:
        file_name = web_url.split("/")[-2].replace("+", "_").replace(" ", "_") + "__"
    
    file_name += pdf.headers.get('Content-Disposition').split('filename=', 1)[1].replace('"', '')

    # insert data into database
    result = db.insert(cursor=cursor, table="unia.mhbs", values={"web_url": web_url, "pdf_name": file_name, "folder": "~/mhbai/pdfs/"}, returning_column="id")
    if result.is_error:
        raise Exception(f"Error inserting mhb {web_url} into database: {result.error}")
    if result.data is None:
        raise Exception(f"Error inserting mhb {web_url} into database: no id returned")
    return_id = result.data[0]

    pdf_path = f"pdfs/{return_id}.pdf"

    # save file
    with open(pdf_path, "wb") as file:
        file.write(pdf.content)

@db.cursor_handling(manually_supply_cursor=False)
def download_pdfs(new_links: list, new_only: bool = False, adapt_file_names: bool = False, print: bool = True, cursor: psycopg2.extensions.cursor | None = None) -> None:
    """
    downloads only new mhb pdfs

    Args:
        new_links (list): list of new mhb links
        new_only (bool): whether to only download new links
        adapt_file_names (bool): whether to adapt file names in order to reduce conflicts; filenames still aren't unique e.g. for instrument courses
        print (bool): whether to print progress information
        cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.
    Returns:
        None
    """

    # if only new links should be downloaded, filter the new_links list
    if new_only is True:
        result = db.select(cursor=cursor, table="unia.mhbs", keywords=["web_url"], answer_type=db.ANSWER_TYPE.LIST_ANSWER) # type: ignore
        if result.is_error:
            raise Exception(f"Error fetching existing mhb links from database: {result.error}")
        existing_links = [i["web_url"] for i in result.data]
        new_links = [i for i in new_links if i not in existing_links]
    
    # iterate through all new links with a progress bar
    # for each new url, download the corresponding pdf
    
    if print is True:
        for web_url in tqdm(new_links):
            fetch_pdf(cursor, web_url, adapt_file_names) # type: ignore
    else:
        for web_url in new_links:
            fetch_pdf(cursor, web_url, adapt_file_names) # type: ignore

@db.cursor_handling(manually_supply_cursor=False)
def download_async(new_links: list[str], new_only: bool = False, adapt_file_names: bool = False, cursor: psycopg2.extensions.cursor | None = None) -> None:
    """
    downloads mhb pdfs using multiprocessing

    Args:
        new_links (list): list of new mhb links
        new_only (bool): whether to only download new links
        adapt_file_names (bool): whether to adapt file names in order to reduce conflicts
        cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.
    Returns:
        None
    """
    
    # if only new links should be downloaded, filter the new_links list
    if new_only is True:
        result = db.select(cursor=cursor, table="unia.mhbs", keywords=["web_url"], answer_type=db.ANSWER_TYPE.LIST_ANSWER) # type: ignore
        if result.is_error:
            raise Exception(f"Error fetching existing mhb links from database: {result.error}")
        existing_links = [i["web_url"] for i in result.data]
        new_links = [i for i in new_links if i not in existing_links]

    # nothing to do
    if not new_links:
        return

    # don't create more workers than chunks/tasks
    num_workers = min(cpu_count(), len(new_links))
    urls_per_job = math.ceil(len(new_links) / num_workers)

    # Map the download_pdfs function to the chunks
    # set new_only to False since this is computed globally in download_async to avoid slow code
    with Pool(processes=num_workers) as pool:
        chunks = [new_links[i:i + urls_per_job] for i in range(0, len(new_links), urls_per_job)]
        # use starmap to pass the extra keyword-like args positionally
        results = [pool.apply_async(download_pdfs, args=(chunk, False, adapt_file_names, False)) for chunk in chunks]
        for result in results:
            result.wait()

@DeprecationWarning
def do_everything():
    """
    combines subfunctions by extracting all mhb links and then downloading all mhbs
    """

    data = fetch_valid_urls()
    download_pdfs(data)


@DeprecationWarning
def check_url(url: str) -> bool:
    """
    checks, whether the url is safe to use
    e.g. when it is not a pdf or it is a redirect link, return False

    Args:
        url (str): url to check
    Returns:
        bool: whether the url is safe to use
    """

    if url.startswith("https://mhb.uni-augsburg.de/") and url.endswith(".pdf") and not "redirect" in url and len(url) <= 500:
        return True
    return False


@DeprecationWarning
def download_all_pdfs():
    """
    downloads all mhb pdfs
    """
    with open("uni_a_all_mhbs.json", "r") as file:
        data = json.load(file)
    for index, i in enumerate(data):
        pdf = requests.get(i)
        with open(f"pdfs/{pdf.headers.get('Content-Disposition').split("filename=",1)[1]}", "wb") as file:
            file.write(pdf.content)
        print(index)


@DeprecationWarning
def add_new_pdfs():
    """
    fetches all mhb links and downloads only the new ones
    """
    data = fetch_valid_urls()
    with open("uni_a_all_mhbs.json", "r") as file:
        old_data = json.load(file)

    with open("uni_a_all_mhbs.json", "w") as file:
        json.dump(data, file, indent=4)
    
    new_links = [i for i in data if i not in old_data]

    download_pdfs(new_links)

'''    
# use this to download all mhb pdfs for university of augsburg timed with the pdf urls already fetched
"""start = time.time()
download_all_pdfs()
end = time.time()
print(end - start)"""

# use this to fetch and download all mhb pdfs for university of augsburg
# do_everything()

# use this to only download new mhb pdfs for university of augsburg
add_new_pdfs()
'''