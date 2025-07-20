# mhbai

## Important licensing details
This code is licensed. For commercial usage please contact the developer (the owner of this github).


This code further contains a pdf reader developed by the developer before the 15th of July 2025
Note, that all files containing code of the pdf-reader or read pdfs aren't Open-Source and can't freely be used commercially. 
In case of commercial use, contact the developer.

## Descirption
This project is able to analyse MHBs and compare them as well as their content. 
It is used to compare the courses of two courses of study to evaluate how many ECTS can be used from one course of study in the other one.

Therefore it can be used to see whether changing courses of study or university or starting studying two courses of study makes sense. 
Also it can be useful in the creation of new courses of study or seeing which courses can be added to an existing course of study.

## Additional informations
This project is still in devolepment.

Analyses MHBs

This code further contains a pdf reader developed by the developer before the 15th of July 2025

## File structure
<pre>
mhbai <br>
├──📁 pdfs/                                contains all mhb pdfs
├──📁 web_service/                         webservice, that allows users to interact with the program through a webpage
    ├──📁 backend/                         contains the web_service specific backend
        └──📄 pdf_reader_toc.py            extracts the module codes from the toc of the mhb, as well as information to the modules
    ├──📁 prototyping_pdf_reader           prototypes for a pdf reader -> might be moved out of web_service folder
    └──📄 server.py                        the web api, which interacts with the requests sent from the user
    └──📄 testing.py                       tests the .py files in web_service
├──📁 web_scraping                         contains all files to scrape the mhb pdfs from the universities
    ├──📁 scrape_uni_augsburg              contains all files to scrape the mhbs of the University of Augsburg
        └──📄 uni_a_all_mhbs.json          contains all links of the mhbs extracted by download_files.py
        └──📄 download_files.py            file to recursively find all mhbs from 2018 and newer and download them to ../../pdfs/ (in the code just /pdf since executed via ssh on pi5)
        └──📄 data_processing.py           extracts the important data from all mhbs
        └──📄 cleaning_data.py             cleans the data from data_processing.py
    └──📄 data.json                        holds all the links, that redirect to a course of study
    └──📄 get_unis_fhs_courses_of_study    gets the links to each course of study of all universities in germany
    └──📄 get_books.py                     extract the url for the pdfs from all links that link to a bachelors degree course of study - not finished yet
    └──📄 get_final_books                  not finished yet
└──📄 pdf_extractor.py                     decoding pdfs by reading them as bytes and decoding and decompressing them
</pre>
## Abbreviations
In order to save time and tremendous amounts of energy, some abbreviations are used in this project. <br>
The following table lists all of them. <br>
<table>
  <thead>
    <tr>
      <th>Abbreviation</th>
      <th>Meaning</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>toc</td>
      <td>table of contents</td>
    </tr>
    <tr>
        <td>mhb</td>
        <td>Modulhandbuch</td>
    </tr>
  </tbody>
</table>

<table>
  <thead>
    <tr>
      <th>File abbreviations</th>
      <th>Meaning</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>extr</td>
      <td>pdf_extractor</td>
    </tr>
    <tr>
      <td>prt</td>
      <td>pdf_reader_toc.py</td>
    </tr>
  </tbody>
</table>

## Information about the pdf reader
The pdf reader was created in order to allow for more precise table recogniction and faster extraction of document data as well as all the other stuff.

## Status quo
### Latest changes
- adding new features to pdf_reader_toc.py
  - extracting all module codes from the toc of a mhb
  - extracting information from each module (still in development); already implemented:
    - German title for german mhbs english title for english mhbs
    - ECTS
    - Content (Inhalte)
    - Goals (Lernziele und Kompetenzen)
- testing the speed of data extraction from pdfs in testing.py (partly already removed)
  - time to extract module codes from toc of mhb: < 20ms
  - time to extract title, ects, content, goals module: < 1ms
- adding features to pdf_extractor.py
### TODOs
- combining web_server with backend
- adding options for saving data in csv/xlsx/json etc.
