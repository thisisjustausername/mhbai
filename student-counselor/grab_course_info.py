import threading
from concurrent.futures import ThreadPoolExecutor
import json

import requests
from bs4 import BeautifulSoup

base_url = "https://www.uni-augsburg.de/de/studium/studienangebot/uebersicht/"
unia_url = "https://www.uni-augsburg.de"

session = requests.Session()

result = session.get(base_url)

# parse the content using BeautifulSoup
soup = BeautifulSoup(result.text, 'lxml')

# find table over all study programs
link_container = soup.find("table")
th = link_container.find("thead")
tb = link_container.find("tbody")
columns = [i.text.strip() for i in th.find_all("th")]
rows = tb.find_all("tr")
courses = []
for row in rows:
    cells = row.find_all("td")
    if len(cells) == len(columns):
        courses.append(
            {
                columns[i]: cells[i].text.strip() for i in range(len(columns))
            } | {
                     "language": (href if (href := cells[-1].find("a")) is not None else dict()).get("href", None)
            } | {
                "course_url": cells[0].find("a")["href"]
            })


class TaskTracker:
    """
    Tracks whether all tasks are already finished

    Parameters:
        active (int): number of active tasks
        lock: Locks
        futures: futures
    """

    def __init__(self):
        self.active = 0
        self.lock = threading.Lock()
        self.futures = []
    

    def start_func(self, future) -> int:
        """
        start a thread and update the tracker variables

        Args:
            future: future to start
        Returns:
            int: number of active threads
        """

        with self.lock:
            self.active += 1
        self.futures.append(future)
        return self.active
    

    def finish_work(self) -> None:
        """
        stop tasks after everything finishes
        """

        with self.lock:
            self.active -= 1
            return self.active


tracker = TaskTracker()


def search_courses(executor, courses: list[dict[str, str]]) -> None | Exception:
    """
    Searches for all available files in the specified Digicampus courses.
    This function is RECURRENT.

    Args:
        executor: ThreadPoolExecutor to handle the threads created by search_courses
        courses: List of course URLs to search
    
    Raises:
        requests.exceptions.HTTPError: when status code is not 200
        IndexOutOfBoundsError: when file has no file ending (might be fixed)
    """
    for i in courses:
        course_data = session.get(unia_url + i["course_url"])
        soup = BeautifulSoup(course_data.text, 'lxml')

        # find facts-box
        facts_box = soup.find("div", class_="factsBox-body")
        facts_items = facts_box.find_all("div", class_="factsBox-item")
        facts_items = {name[:-1] if (name:= i.find("span", class_="factsBox-itemLabel").text.strip()).endswith(":") else name: i.find("span", class_="factsBox-itemValue").text.strip() for i in facts_items}

        facts_urls = facts_box.find_all("a", class_="linkColumns-columnLink")
        facts_urls = dict((i.text.strip(), i["href"]) for i in facts_urls)
        

        contents = soup.find_all("div", class_="textEditorContent")
        content = "\n".join([t for p in contents[0].find_all("p") if ( t := p.text.strip()) != "&nbsp;"])

        perspectives = [i.text.strip() for i in contents[1].find_all("li", class_="bulletList-item--small-margin")]

        i["facts_items"] = facts_items
        i["facts_urls"] = facts_urls
        i["content"] = content
        i["perspectives"] = perspectives
        i["base"] = course_data.text


        # urls = 
        # contacts = 


def search_threaded(courses: list[dict[str, str]]) -> None: # list[dict[str, str | list[str] | list[dict[str, str]]]]:
    """
    Searches for all available files in the specified Digicampus courses.
    Handles the threading of the threads created by search_files.

    Args:
        courses (list[dict[str, str]]): List of course URLs to search

    Returns:
        list[dict[str, str | list[str] | list[dict[str, str]]]]: List of course data with facts, urls, content and perspectives
    """
 
    num_workers = 10

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        executor.submit(search_courses, executor, courses).result()
        results = []
        for i in tracker.futures:
            # results.extend(i.result())
            pass
        
    # return results


import re

def clean_spaces(obj):
    if isinstance(obj, dict):
        return {k: clean_spaces(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [clean_spaces(item) for item in obj]

    elif isinstance(obj, str):
        return re.sub(r"\s+", " ", obj).strip()

    else:
        return obj


if __name__ == "__main__":
    search_threaded(courses)
    courses = clean_spaces(courses)

    courses = [{k: v for k, v in i.items() if not isinstance(v, dict) and k not in ["base"]} | i["facts_items"] | i["facts_urls"] for i in courses]
    
    with open("student-counselor/course_data.json", "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=4, ensure_ascii=False)

    print(json.dumps([dict((k, v) for k, v in i.items() if k not in ["base"]) for i in courses], indent=4, ensure_ascii=False))