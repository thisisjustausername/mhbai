# mhbai

## Important licensing details
This code is licensed. For commercial usage please contact the developer (the owner of this github).

## Descirption
Analyses MHBs

This code further contains a pdf reader developed by the developer before the 15th of July 2025

## File structure
<pre>
mhbai <br>
├──📁 pdfs/                          contains all mhb pdfs
├──📁 web_service/                   webservice, that allows users to interact with the program through a webpage
    ├──📁 backend/                   contains the web_service specific backend
    ├──📁 prototyping_pdf_reader     prototypes for a pdf reader -> might be moved out of web_service folder
    └──📄 server.py                  the web api, which interacts with the requests sent from the user
├──📁 web_scraping                   contains all files to scrape the mhb pdfs from the universities
    ├──📁 scrape_uni_augsburg        contains all files to scrape the mhbs of the University of Augsburg
        └──📄 uni_a_all_mhbs.json    contains all links of the mhbs extracted by download_files.py
        └──📄 download_files.py      file to recursively find all mhbs from 2018 and newer and download them to ../../pdfs/ (in the code just /pdf since executed via ssh on pi5)
    └──📄 data.json                  
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
    
  </tbody>
</table>