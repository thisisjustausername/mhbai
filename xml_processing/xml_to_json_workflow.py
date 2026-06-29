import json
import os
from pathlib import Path
import xmltodict
from xml_processing import xml_to_json, find_information
from multiprocessing import Pool, cpu_count
from tqdm import tqdm


base_read_path = Path(os.path.expanduser("~/mhbai/mount/StudisDaten/Modulhandbuecher/"))
base_save_path = Path(os.path.expanduser("~/mhbai/uni-a_mhbs_json/"))

def process_file(xml_file: str):
    with open(xml_file, "r") as f:
        xml = f.read()
    # print(xml_file)
    diction = xmltodict.parse(xml)
    data = xml_to_json.clean_html_dict(xml_to_json.clean_dict(diction))
    result = find_information.clean_mhb(data) # type: ignore
    return xml_file, result

def main():
    files = [str(i) for i in base_read_path.rglob("*.xml")]

    with Pool(processes=cpu_count()) as pool:
        for xml_file, result in tqdm(
            pool.imap_unordered(process_file, files), total=len(files)
        ):
            
            save_path = base_save_path / Path(xml_file).relative_to(base_read_path).with_suffix(".json")
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "w") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
    # for i in base_read_path.rglob("*.xml"):
    #     print(i)
    #     process_file(str(i))