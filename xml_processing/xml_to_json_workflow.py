from xml_processing import xml_to_json, find_information


# 1. read xml
with open("test.xml", "r") as f:
    xml = f.read()

# 2. parse xml to json
diction = xml_to_json.xmltodict.parse(xml)

# 3. clean json by replacing html with its content
data = xml_to_json.clean_html_dict(xml_to_json.clean_dict(diction))

