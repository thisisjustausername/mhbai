# Processes

This documentation lists all processes that run regularly.

## Specific for University of Augsburg

0. [Extracting information from XML-MHBs](#xml-extraction)
1. [Downloading mhbs](#fetch-mhbs)
2. [Extracting raw module pages from mhbs and saving them to the db](#raw-pages)
3. [Extracting module information from mhbs using regex and saving data to db](#regex-extraction)
4. [Extracting module information using ai and saving data to db](#ai-extraction)
5. [Extracting course of study information from unia website](#uni-a-website-extraction)
6. [Extract MHB and module information from studis and save it to mongodb](#mhb-and-module-extraction-from-studis)


### XML Extraction

In order to extract the data from all module handbooks in XMl format of the University of Augsburg, use this way of computation.<br/>
It is cheap, fast and deterministic with very high accuracy and the option to add optional ML computing.
```bash
source venv/bin/activate
python3 -m 
```


### Fetch MHBs

Download the MHB-PDFs from the University of Augsburg from <https://mhb.uni-augsburg.de>.
Specify `1` for only downloading new pdfs and `0` for downloading all available pdfs.

```bash
source venv/bin/activate
python3 -m university_of_augsburg.web_scraping.download_files 1
```

### Raw pages

Extract raw pages from MHB-PDFs from the University of Augsburg.</br>
Only run this program after downloading all needed MHB-PDFs using [Fetch MHBs](#fetch-mhbs).

```bash
source venv/bin/activate
python3 -m database.add_to_db.add_modules_raw
```

### Regex Extraction

Extract module information from MHB-PDFs using regex.</br>
Only run this program after downloading all needed MHB-PDFs using [Fetch MHBs](#fetch-mhbs).

```bash
source venv/bin/activate
python3 -m database.add_to_db.add_modules_regex
```

### AI Extraction

Extract module information from MHB-PDFs using AI (by default llama3:3b).</br>
Only run this program after downloading all needed MHB-PDFs using [Fetch MHBs](#fetch-mhbs) and fetching all raw module pages using [Raw pages](#raw-pages).

```bash
source venv/bin/activate
python3 -m ai.overall_ai.full_extraction
```

### Uni-A Website Extraction

Extract information about courses of study from the University of Augsburg website (NOT FINISHED YET).</br>
This information is embedded and stored in a chromadb database.</br>

```bash
source venv/bin/activate
python3 -m student_counselor.grab_course_info
python3 -m student_counselor.json_to_text
python3 -m student_counselor.embed
```

### MHB and Module Extraction from Studis

Extract MHB and module information from Studis and save it to MongoDB.</br>
The XML-files from Studis are first parsed into JSON-files, these are then cleaned, then information is extracted into a new compressed schema from which information is saved to MongoDB.</br>
An alternative approach generating a more detailed schema is also available under `xml_processing/pipeline.py`.</br>

```bash
source venv/bin/activate
python3 -m xml_processing.xml_to_json_workflow
python3 -m xml_processing.compress_pipeline
python3 -m mongo_db.fill_db
```

When first using mongoDB, initialize it first as follows:

```bash
source venv/bin/activate
python3 -m mongo_db.create_user
python3 -m mongo_db.create_collection
```

## Website and API
