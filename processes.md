# Processes

This documentation lists all processes that run regularly.

## Specific for University of Augsburg

1. [Downloading mhbs](#fetch-mhbs)
2. [Extracting raw module pages from mhbs and saving them to the db](#raw-pages)
3. [Extracting module information from mhbs using regex and saving data to db](#regex-extraction)
4. [Extracting module information using ai and saving data to db](#ai-extraction)

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

## Website and API

