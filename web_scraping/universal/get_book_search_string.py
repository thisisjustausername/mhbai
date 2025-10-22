# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: create search string for search engine from course information, code works but needs to be polished, use lxml
# Status: IN DEVELOPMENT
# TODO: instead of single process for each link fetch, use multiple link fetch
# TODO: save error links

import json
import math
import requests
import multiprocessing
import functools
import inspect

with open("data.json", "r") as file:
    data = json.loads(file.read())

# NOTE: doesn't work with Queue, since instead of returning has to put into queue
def catch_error(func):
    """
    Decorator to catch and log errors in a function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        wrapper function to execute the decorated function with error handling.
        """
        bound = inspect.signature(func).bind(*args, **kwargs)
        bound.apply_defaults()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error occurred for links {bound.arguments.get('links', [])}")
            return [{"success": False, "link": i, "error": str(e)} for i in bound.arguments.get("links", [])]
    return wrapper

@catch_error
def create_links(links: list[str], bachelor_only: bool=False) -> None | str | Exception:
    """
    Create a search string for a course link
    
    Parameters:
        links (list[str]): The URLs of the course pages.
        bachelor_only (bool): Whether to filter for bachelor courses only.
    """
    results = []
    for link in links:
        website = requests.get(link)
        if bachelor_only:
            if "Abschluss</strong>: Bachelor" not in website.text:
                return None
        text = website.text
        link_full = text.split("Zur Webseite &gt")[-2].split("href=")[-1]
        try:
            correct_link = link_full.split("dest")[1].split("www.")[1].split(".de")[0] + ".de"
        except IndexError:
            try:
                correct_link = link_full.split("dest")[1].split("www.")[1].split('" target')[0]
            except Exception as e:
                print(f"Error occurred for link {link}")
                results.append({
                    "success": False, 
                    "link": link, 
                    "error": str(e)})
        title = text.split('<h1 title="')[1].split('">')[0]
        print(correct_link, title)
        result = f"page:{correct_link} filetype:pdf modulhandbuch {title}"
        results.append({
            "success": True, 
            "link": link, 
            "uni_link": correct_link, 
            "search_string": result, 
            "title": title})
    return results


def get_search_strings(urls_per_job: int = 5):
    """
    Get the search strings for all courses of study from studieren.de
    A search string looks like this: "page:<uni.de> filetype:pdf modulhandbuch <course title>"
    Parameters:
        urls_per_job (int): Number of URLs to be processed per job in the multiprocessing pool.
    Returns: 
        None
    """
    multiprocessing.set_start_method("spawn")
    with open("web_scraping/universal/files/data.json", "r") as file:
        list_urls = json.load(file)
    processes = math.ceil(len(list_urls) / urls_per_job)
    with multiprocessing.Pool(processes=processes) as pool:
        all_elements = []
        all_errors = []
        results = [pool.apply_async(create_links, args=(list_urls[i:i + urls_per_job],)) for i in range(0, len(list_urls), urls_per_job)]
        for result in results:
            elements, error_list = result.get()
            all_elements += elements
            all_errors += error_list

    with open("web_scraping/universal/files/data.json", "w") as file:
        json.dump(all_elements, file, indent=4)
    with open("web_scraping/universal/files/error_list.json", "w") as file:
        json.dump(all_errors, file, indent=4)

def get_error_base_links(urls_per_job: int = 1):
    """
    Get the base links for all courses of study from studieren.de where errors occurred.
    
    Parameters:
        urls_per_job (int): Number of URLs to be processed per job in the multiprocessing pool.
    """
    multiprocessing.set_start_method("spawn")
    with open("web_scraping/universal/files/data.json", "r") as file:
        all_elements = json.load(file)
    with open("web_scraping/universal/files/error_list.json", "r") as file:
        list_urls = json.load(file)
    processes = math.ceil(len(list_urls) / urls_per_job)
    with multiprocessing.Pool(processes=processes) as pool:
        all_errors = [] # initializing all_errors new, but not all_elements
        results = [pool.apply_async(process_urls, args=(list_urls[i:i + urls_per_job],i,)) for i in range(0, len(list_urls), urls_per_job)]
        for result in results:
            elements, error_list = result.get()
            all_elements += elements
            all_errors += error_list
    with open("web_scraping/universal/files/data.json", "w") as file:
        json.dump(all_elements, file, indent=4)
    with open("web_scraping/universal/files/error_list.json", "w") as file:
        json.dump(all_errors, file, indent=4)   

if __name__ == "__main__":
    get_base_links(urls_per_job=5)
    print("-----------------------------------------------\nstep 2\n-----------------------------------------------")
    with open("web_scraping/universal/files/data.json", "r") as file:
        data = json.load(file)
    print(len(data))