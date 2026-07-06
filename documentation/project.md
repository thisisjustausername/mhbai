# Project overview
Documentation for project goals and use cases. Below we specify example use cases combined with their technical realisation structure.

## Examination Office
* automate credit validation
### Realisation
1. [Data Scraping](#data-scraping)
2. [Data Extraction and Preprocessing](#data-extraction-and-preprocessing)
3. Create graph of modules and study programs
4. Label data by using sequence entity recognition to find similar labeled data and label. the results manually
5. Train a model to predict credit validation based on the graph and the labeled data (using Transformer model with regression head for finetuning, e.g. transforming input)

## Student Advice and Counselling Service
* Increase efficiency in advising students and soon to become students
<hr>

## Academic advisor
* Compute module difference between study programs
* Generate module descriptions
* Check for inconsistencies in modules and MHBs
<hr>

## Students
* Compare study programs (also interactively)
* Receive personalized information for change of program, etc.
<hr>
* Counselling assistant on website

## Comparison portal
* More precise comparsion of study programs
* Detailed information about content and main focus of study programs
<hr>


# Data Scraping
1. Scrape MHBs and modules from all universities as well as study program descriptions and POs.
2. Use a Search Enginge combined with a LLM-Crawler and tools like Subdomain-Enumeration.

# Data Extraction and Preprocessing
1. Extract the data from PDFs and XML- and HTML-documents using various techniques<br/>
    For XML (from STUDIS) use a parser with deterministic and computationally cheap methods like regex to extract important data<br/>
    For PDF use following workflow: PDF -> MinerU -> Markdown -> LLM -> SQL oder falls LLm fehlschlägt ... -> LLM -> Fehler -> Agentic workflow -> SQL<br/>
    We will not further describe the agent workflow.
2. Validate the data using Regex, NER, Sequence-ER and Zero-Shot in order to find similar text in the original data and compare whether the result makes sense.