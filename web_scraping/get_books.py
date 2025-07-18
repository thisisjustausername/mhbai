import json
import requests
from multiprocessing import Process, Queue

with open("data.json", "r") as file:
    data = json.loads(file.read())

def create_link(link, queue):
    website = requests.get(link)
    if "Abschluss</strong>: Bachelor" not in website.text:
        return None
    text = website.text
    link_full = text.split("Zur Webseite &gt")[-2].split("href=")[-1]
    try:
        correct_link = link_full.split("dest")[1].split("www.")[1].split(".de")[0] + ".de"
    except IndexError:
        print("\033[91mError occured\033[0m")
        try:
            correct_link = link_full.split("dest")[1].split("www.")[1].split('" target')[0]
        except:
            return None
    title = text.split('<h1 title="')[1].split('">')[0]
    print(correct_link, title)
    queue.put(f"page:{correct_link} filetype:pdf modulhandbuch {title}")

processes = []
q = Queue()
for i in data:
    p = Process(target=create_link, args=(i, q))
    p.start()
    processes.append(p)

for p in processes:
    p.join()

results = [q.get() for p in processes]
print(results)

with open("data_search.json", "w") as file:
    json.dump(results, file)