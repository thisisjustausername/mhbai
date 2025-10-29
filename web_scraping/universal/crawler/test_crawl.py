# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: crawl a web page and return all the urls it contains
# STATUS: Brainstorming

# NOTE: remove already fetched urls, make graph to tree
# combine crawler with instant api from duckduckgo and filter the crawler results with mhb modulhandb

from multiprocessing.pool import Pool
import requests
from multiprocessing import JoinableQueue, Manager, Process, Queue, cpu_count
from urllib.parse import urljoin
from lxml import html


def crawl(url: str, depth: int = 0, queue: Queue = None) -> dict[str, int | list[str] | str]:
    """
    Crawl a web page and return all the urls it contains.

    Parameters:
        url (str): The URL of the web page to crawl.
        depth (int): The depth of crawling. Default is 0 (only the given page).
        queue (Queue): A multiprocessing Queue to store results. If not None, results will be put into the queue.
    Returns:
        dict[str, int | list[str] | str]: A dictionary containing the URLs found on the page, the depth, and the parent URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
    except requests.RequestException as e:
        return {"urls": [], "depth": depth + 1, "parent_url": url}
    tree = html.fromstring(response.content)

    # Extract href attributes from all <a> tags
    hrefs = tree.xpath('//a/@href')

    # Normalize partial URLs
    urls = {urljoin(url, href) for href in hrefs if href}
    data = {"urls": list(urls), "depth": depth + 1, "parent_url": url}
    if queue is not None:
        queue.put(data)
    return data

def batch_crawl(urls: list[str], depth: int, queue: Queue = None) -> list[str]:
    """
    Crawl a batch of web pages of a specific depth and return all the urls they contain.

    Parameters:
        urls (list[str]): A list of URLs of the web pages to crawl.
        depth (int): The depth of crawling.
        queue (Queue): A multiprocessing Queue to store results. If not None, results will be put into the queue.
    Returns:
        dict[str, int | list[str] | str]: A dictionary containing the URLs found on the pages, the depth, and the parent URL.
    """
    """results = {"urls": [], "depth": depth+1, "parent_url": "url"}
    for url in urls:
        results["urls"] += crawl(url, depth=depth)["urls"]
    if queue is not None:
        queue.put(results)
    return results"""
    results = {"urls": [], "depth": depth+1, "parent_url": "url"}
    with Pool(cpu_count()) as pool:
        # map crawl function across all urls
        batch_results = pool.starmap(crawl, [(url, depth) for url in urls])
    # collect results
    for r in batch_results:
        results["urls"] += r["urls"]
    results["urls"] = list(set(results["urls"]))  # remove duplicates
    if queue is not None:
        queue.put(results)
    return results


def worker(task_q: JoinableQueue, seen, max_depth: int):
    """
    Worker loop that pulls (url, depth) from the queue, processes it and enqueues children.
    Stops when it receives `None` from the queue (sentinel).
    """
    while True:
        item = task_q.get()
        if item is None:
            # Sentinel received -> stop the worker
            task_q.task_done()  # mark sentinel consumed if you want to keep task accounting consistent
            break

        url, depth = item["url"], item["depth"]
        try:
            # Avoid revisiting
            if url in seen:
                task_q.task_done()
                continue

            seen[url] = True  # mark visited (Manager dict acts like a shared set)
            # Do the actual crawl work (replace with your real function)
            children = crawl_url(url)

            # Enqueue children if we haven't reached max depth
            if depth < max_depth:
                for child in children:
                    if child not in seen:
                        task_q.put((child, depth + 1))
        except Exception:
            # Log/handle exceptions as needed
            pass
        finally:
            task_q.task_done()

# partially inefficient, since only asynchronous per batch
def recursive_crawl_synchr(url: str, max_depth: int) -> set[str]:
    """
    Recursively crawl a web page up to a specified depth using synchronous calls.
    Not implemented yet.

    Parameters:
        url (str): The URL of the web page to crawl.
        max_depth (int): The maximum depth to crawl.
    Returns:
        set: A set of URLs found during the crawl.
    """
    found_urls = set()
    data = crawl(url, depth=0)

    # set new urls
    new_urls = set(data["urls"]) - found_urls

    # update overall found urls
    found_urls.update(data["urls"])

    for i in range(1, max_depth):
        result = batch_crawl(list(new_urls), depth=i)
        new_urls = set(result["urls"]) - found_urls
        new_urls = {link for link in new_urls if link.startswith("http")}
        found_urls.update(result["urls"])
    return found_urls

# NOTE: prototype, too slow for real use
@DeprecationWarning
def recursive_crawl(url: str, max_depth: int) -> set:
    """
    Recursively crawl a web page up to a specified depth.

    Parameters:
        url (str): The URL of the web page to crawl.
        max_depth (int): The maximum depth to crawl.
    Returns:
        set: A set of URLs found during the crawl.
    """

    # initialize Queue
    q = Queue()
    workers = []
    finished_workers = 0
    
    # initialize first crawl
    """p = Process(target=workers, kwargs={"queue": q, "url": url, "depth": 0})
    p.start()
    workers.append(p)"""
    initial_data = crawl(url, depth=0, queue=q)

    # crawl until all workers are finished
    for i in initial_data["urls"]:
        p = Process(target=crawl, kwargs={"url": i, "depth": 1, "queue": q})
        p.start()
        workers.append(p)
    
    while not q.empty() or any(p.is_alive() for p in workers):
        data = q.get()
        if data["depth"] < max_depth:
            for link in data["urls"]:
                p = Process(target=crawl, kwargs={"url": link, "depth": data["depth"], "queue": q})
                p.start()
                workers.append(p)
    for p in workers:
        p.join()

def recursive_crawl_cpu(url: str, max_depth: int) -> set:
    """
    Recursively crawl a web page up to a specified depth using multiprocessing.
    Instead of trying to be optimal, it only runs the 2nd level of crawling in parallel, assuming all branches take approximately the same time.
    It also assumes that the number of links on the first page is larger than the number of CPU cores but not excessively large.
    These are cons for using this function, but greatly simplify the implementation.

    Parameters:
        url (str): The URL of the web page to crawl.
        max_depth (int): The maximum depth to crawl.
    Returns:
        set: A set of URLs found during the crawl.
    """
    raise NotImplementedError("This function is not implemented yet.")

@DeprecationWarning
def recursive_crawl_batch(url: str, max_depth: int) -> list[str]:
    """
    Recursively crawl a web page up to a specified depth using batch processing.
    Using one process for each list of urls by output of another process.

    Parameters:
        url (str): The URL of the web page to crawl.
        max_depth (int): The maximum depth to crawl.
    Returns:
        list[str]: A list of URLs found during the crawl.
    """
    # initialize Queue
    q = Queue()
    workers = []
    
    # initialize first crawl
    """p = Process(target=workers, kwargs={"queue": q, "url": url, "depth": 0})
    p.start()
    workers.append(p)"""
    initial_data = crawl(url, depth=0, queue=q)

    # crawl until all workers are finished
    p = Process(target=batch_crawl, kwargs={"urls": initial_data["urls"], "depth": 1, "queue": q})
    p.start()
    workers.append(p)
    
    while not q.empty() or any(p.is_alive() for p in workers):
        data = q.get()
        if data["depth"] < max_depth:
            p = Process(target=batch_crawl, kwargs={"urls": data["urls"], "depth": data["depth"], "queue": q})
            p.start()
            workers.append(p)
    for p in workers:
        p.join()

def recursive_crawl_pool(url: str, max_depth: int) -> set:
    """
    Recursively crawl a web page up to a specified depth using multiprocessing Pool.
    Not implemented yet.

    Parameters:
        url (str): The URL of the web page to crawl.
        max_depth (int): The maximum depth to crawl.
    Returns:
        set: A set of URLs found during the crawl.
    """
    worker_count = cpu_count()
    manager = Manager()
    seen = manager.dict()

    task_queue = JoinableQueue()
    workers = []

    for _ in range(worker_count):
        pass

def filter(urls: set[str]) -> set[str]:
    """
    Filter a set of URLs to only include those that are likely to be MHB pages.
    Only German filters are added at this point.
    Parameters:
        urls (set[str]): A set of URLs to filter.
    Returns:
        set[str]: A filtered set of URLs.
    """
    return {url for url in urls if "mhb" in url or "modulhandb" in url}

if __name__ == "__main__":
    test_url = "https://www.uni-regensburg.de/"
    test_url = "https://www.uni-augsburg.de"
    """result = recursive_crawl_batch(test_url, max_depth=2)
    for link in result:
        print(link)"""
    found_urls = recursive_crawl_synchr(url=test_url, max_depth=2)
    response = filter(found_urls)
    # now choose link, which is most often hit by the other urls
    print(response)