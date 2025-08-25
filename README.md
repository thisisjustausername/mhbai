# mhbai

## Important licensing details
This code is licensed. For commercial usage please contact the developer (the owner of this github).


This code further contains a pdf reader developed by the developer before the 15th of July 2025
Note, that all files containing code of the pdf-reader or read pdfs aren't Open-Source and can't freely be used commercially. 
In case of commercial use, contact the developer.

## Description
This project is able to analyse MHBs and compare them as well as their content. 
It is used to compare the courses of two courses of study to evaluate how many ECTS can be used from one course of study in the other one.

Therefore it can be used to see whether changing courses of study or university or starting studying two courses of study makes sense. 
Also it can be useful in the creation of new courses of study or seeing which courses can be added to an existing course of study.

## Additional informations
This project is still in devolepment.

Analyses MHBs

This code further contains a pdf reader developed by the developer before the 15th of July 2025

## File structure
### short variant (older)
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
    └──📄 pdf_data.json                    holds the extracted infos about the courses of study and modules
    └──📄 clean_module_infos.json          holds the cleaned data of module infos
    └──📄 complete_information.json        holds cleaned and complete data of module infos
    └──📄 get_unis_fhs_courses_of_study    gets the links to each course of study of all universities in germany
    └──📄 get_books.py                     extract the url for the pdfs from all links that link to a bachelors degree course of study - not finished yet
    └──📄 get_final_books                  not finished yet
└──📄 pdf_extractor.py                     decoding pdfs by reading them as bytes and decoding and decompressing them
</pre>
### long variant (new)
<pre>
└──📄 LICENSE                                    
└──📄 uni_augsburg_error_files.json              
└──📄 test.md (local file)                       
├──📁 documentation/                             
│   └──📄 visualize_file_structure.py            turns the filestructure into a markdown representation with added descriptions     
└──📄 .gitattributes                             
└──📄 .gitignore                                 
└──📄 mhb_overlaps.json                          
└──📄 university_of_hamburg.json                 
└──📄 README.md                                  
└──📄 test.html (local file)                     
└──📄 test.csv (local file)                      
├──📁 web_scraping/                              
│   ├──📁 rwth_aachen/                           
│   │   └──📄 rwth_aachen_errors.json            
│   │   └──📄 scrape_uni.py                      find the urls to the mhbs for university of aachen
│   │   └──📄 download_mhbs.py                   dowload mhbs from urls and save them as pdfs
│   │   └──📄 rwth_aachen.json                   
│   └──📄 data.json                              
│   └──📄 get_final_books.py                     
│   ├──📁 scrape_uni_augsburg/                   
│   │   └──📄 data_processing.py                 extract data from pdfs and save them in json, clean data afterwards using cleaning_data.py
│   │   └──📄 download_files.py                  download mhbs from University of Augsburg
│   │   └──📄 uni_a_all_mhbs.json                
│   │   └──📄 links_information.json             
│   │   └──📄 retrieve_link_info.py              retrieve links for downloading the pdfs since they are different from the ones copied by the user
│   │   └──📄 cleaning_data.py                   clean data, execute after data_processing.py
│   └──📄 get_books.py                           create search string for search engine from course information, code works but needs to be polished, use lxml
│   ├──📁 university_of_hamburg/                 
│   │   └──📄 courses_of_study.json              
│   │   └──📄 search_mhbs.py                     
│   │   └──📄 scrape_mhbs_hamburg.py             find all courses of study of the University of Hamburg
│   │   └──📄 university_of_hamburg.json         
│   │   └──📄 download_mhbs.py                   extract urls for MHBs from Univeristy of Hamburg using search engine
│   │   └──📄 cleaning.py                        
│   │   └──📄 university_of_hamburg_errors.json  
│   │   └──📄 table_data_all_courses.txt         
│   └──📄 get_unis_fhs_courses_of_study.py       get the base urls for all courses of study
└──📄 university_of_hamburg_errors.json          
└──📄 pyvenv.cfg (local file)                    
├──📁 pdf_reader/                                
│   └──📄 pdf_extractor.py                       read content and extract objects from pdfs
│   └──📄 pdf_reader_toc.py                      extracts information from MHBs, specifically taylored for MHBs from the University of Augsburg
│   └──📄 __init__.py                            
│   └──📄 Type_Checker.py                        type checker
│   └──📄 testing.py                             
│   └──📄 MHB_Overlaps.py                        dataclass for MHB overlaps
│   └──📄 MHB.py                                 dataclass for MHB
└──📄 local_setup.md                             
└──📄 license_header.txt                         
└──📄 uni_augsburg_module_data.json              
├──📁 web_service/                               
│   └──📄 server.py                              website for comparing MHBs or seeing MHB information for MBS of the University of Augsburg
│   └──📄 __init__.py                            
│   └──📄 uni_augsburg_look_up.json              
│   ├──📁 backend/
│   │   └──📄 test_pdf.pdf                       
│   │   └──📄 geo_test.pdf                       
│   │   ├──📁 prototyping_pdf_reader/            
│   │   │   └──📄 stream_to_pdf.py               
│   │   │   └──📄 recreate_pdf.py                
│   │   │   └──📄 rendered_pdf_page.pdf          
│   │   │   └──📄 pdf_part1.txt                  
│   │   │   └──📄 output.pdf                     
│   │   │   └──📄 pdf_test.py                    
│   │   │   └──📄 test.py                        
│   │   │   └──📄 part_of_pdf.txt                
│   │   │   └──📄 pdf_reader_prototype.py        
│   ├──📁 static/                                
│   │   └──📄 styles.css                         
│   │   └──📄 favicon.ico                        
│   └──📄 testing.py                             used for testing the website in server.py
│   ├──📁 templates/                             
│   │   └──📄 home.html                          
│   │   └──📄 test.html (local file)             
├──📁 extract_info/                              
│   └──📄 __init__.py                            
│   └──📄 check_errors.py                        Unspecified
│   └──📄 extract_info_augsburg.py               save data from MHB to json
└──📄 main.py                                    
└──📄 mhb.json
</pre>

## Python documentation
Each python file starts with a License header.<br>
Next a one line description follows, describing the task of the file.<br>
After that a one line status follows, describing whether the file is IN DEVELOPMENT, FINISHED, ...<br>
Important notes follow afterwards indicated by: IMPORTANT NOTE:<br>
After that important TODOs follow.<br>
For docstrings the numpy format is used

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
- working on byte to string decryption (not finished yet)
- implementing export functions for csv, html, md, txt
- scraping mhbs from other universities
- testing ultimate tools to extract mhbs from all universities no matter their internal website structure (first tests successful)
- bug-fixes in pdf_reader_toc.py making reading mhbs more resilient to "irregular" pdfs

### TODOs
- combining web_server with backend
- adding options for saving data in csv/xlsx/json etc.
- update file structure in README for web_service
- finish commenting pdf_reader_toc.py
- enable the export button in home.html just when the data is loaded
- test exporting
- important bug-fix. For pages always the pages of the shortest module are used. For the website and export, show the pages for all mhbs and specify which page list correlates to which mhb
- restructure file structure to make it more intuitiv
- in MHB_Overlaps instead of choosing name, choose title and mention date of MHB