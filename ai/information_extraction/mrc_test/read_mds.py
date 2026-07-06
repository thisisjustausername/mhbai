import os
import re
import pandas as pd
from IPython.display import display


# setting variables
path = os.path.expanduser("~/mhbai/ai/information_extraction/mrc_test/markdown/")
min_lines = 100

# fetching files
files = [os.path.join(path, i) for i in os.listdir(path)]

# filtering files
long_files = []
for i in files:
    with open(i, "r") as f:
        data = f.read()
    if len(data.split("\n")) < min_lines:
        continue
    
    heading_contents = []
    heading = i.split("/markdown/", 1)[1][:-3]
    content = []
    for line in data.split("\n"):
        line = line.strip()
        if re.match(r'(?m)^#+ .*', line):
            heading_contents.append({"heading": heading.strip(), "content": "\n".join(content).strip()})
            heading = line.split(" ", 1)[1]
            content = []
            continue
        content.append(line)
    heading_contents.append({"heading": heading.strip(), "content": "\n".join(content).strip()})

    long_files.append({"file_name": i, "content": data, "headings": heading_contents})
print(f"Number of files:   {len(long_files)}")

print(f"Overall elements:  {sum([len(i["headings"]) for i in long_files])}")
print(f"Distinct contents: {len(set(e["content"] for i in long_files for e in i["headings"]))}")
print(f"Distinct headings: {len(set(e["heading"] for i in long_files for e in i["headings"]))}")

pairs = [(e["heading"], e["content"], i["content"], i["file_name"]) for i in long_files for e in i["headings"]]
df = pd.DataFrame(pairs, columns=["heading", "content", "file_data", "file_name"])
df["heading_short"] = df["heading"].apply(lambda x: x.split("(", 1)[0].split("{", 1)[0].split("![", 1)[0].split("`", 1)[0].strip())
df["content"] = df["content"].apply(lambda x: x.split("(", 1)[0].split("{", 1)[0].split("![", 1)[0].split("`", 1)[0].strip())
df = df[(df["heading_short"] != "") & (df["content"] != "")]

 
print(f"Overall results:   {len(df)}")

pd.set_option('display.max_columns', None)
display(df.head(10))

df.to_pickle(path=os.path.expanduser("~/mhbai/ai/information_extraction/mrc_test/headings.pkl"))

# Process files
# for each file add a clean text version that is used for llm query generation
