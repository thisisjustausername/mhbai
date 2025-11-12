# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: Deprecated way of creating search strings for mhbs, slow
# Status: DEPRECATED
# FileID: Sc-ge-0008


# TODO: instead of single process for each link fetch, use multiple link fetch
# TODO: save error links

import json
import requests
from multiprocessing import Process, Queue
import functools
import inspect

with open("data.json", "r") as file:
    data = json.loads(file.read())

# NOTE: doesn't work with Queue, since instead of returning has to put into queue
def catch_errors(func):
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
            return func(*args, **kwargs), None
        except Exception as e:
            print(f"Error occurred in {func.__name__}: {e}")
            return None, bound.arguments.get("link")
    return wrapper

@catch_errors
def create_link(link: str, queue: Queue, bachelor_only: bool=False) -> None | str | Exception:
    """
    Create a search string for a course link
    
    Parameters:
        link (str): The URL of the course page.
        queue (multiprocessing.Queue): Queue to store the resulting search string.
        bachelor_only (bool): Whether to filter for bachelor courses only.
    """
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
            raise e
    title = text.split('<h1 title="')[1].split('">')[0]
    print(correct_link, title)
    queue.put(f"page:{correct_link} filetype:pdf modulhandbuch {title}")


if __name__ == "__main__":
    processes = []
    q = Queue()
    for i in data:
        p = Process(target=create_link, args=(i, q))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    results = [q.get() for _ in processes]
    successful_results = [i[0] for i in results]
    errors = [i[1] for i in results]
    print(successful_results)

    with open("web_scraping/universal/files/get_books_data_search.json", "w") as file:
        json.dump(successful_results, file, indent=4)

    with open("web_scraping/universal/files/get_books_data_errors.json", "w") as file:
        json.dump(errors, file, indent=4)