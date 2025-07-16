import requests
import json
from bs4 import BeautifulSoup
import time

def check_url(url: str) -> bool:
    """check_url \n
    checks, whether the url is safe to use"""

    if url.startswith("https://mhb.uni-augsburg.de/") and url.endswith(".pdf") and not "redirect" in url and len(url) <= 500:
        return True
    return False

def fetch_valid_urls(url_list=["https://mhb.uni-augsburg.de/"], final_links=[]):
    """fetch_valid_urls \n
    searches for all mhb links and saves them as valid urls"""

    # start_url = "https://mhb.uni-augsburg.de/"
    new_urls = []
    for link in url_list:
        result = requests.get(link)
        if result.status_code != 200:
            raise Exception("Error fetching mhb links")

        soup = BeautifulSoup(result.text, 'lxml')

        link_container = soup.find("div", class_="section-inner mt-0 mb-0")

        # next line is optional
        link_container = link_container.find("div", class_="textEditorContent")

        list_items = link_container.find_all('li')
        links = [i.find('a')['href'] for i in list_items]
        links = [link + i for i in links]

        # iterate from the end in order to not change the next indices when popping an element from the list
        for curr_link in links:
            if curr_link.endswith(".pdf"):
                final_links.append(curr_link)
            else:
                new_urls.append(curr_link)
    if len(new_urls) == 0:
        return final_links
    return fetch_valid_urls(new_urls, final_links)

def download_all_pdfs():
    with open("uni_a_all_mhbs.json", "r") as file:
        data = json.load(file)
    for index, i in enumerate(data):
        pdf = requests.get(i)
        with open(f"pdfs/{pdf.headers.get('Content-Disposition').split("filename=",1)[1]}", "wb") as file:
            file.write(pdf.content)
        print(index)



if __name__ == "__main__":
    def do_everything():
        data = fetch_valid_urls()
        print(f"It took approximately {time.time() - start} seconds to fetch all mhbs of the Uni Augsburg.")
        with open("uni_a_all_mhbs.json", "w") as file:
            json.dump(data, file)

        download_all_pdfs()

    start = time.time()
    download_all_pdfs()
    end = time.time()
    print(end - start)