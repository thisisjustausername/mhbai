# Information Extraction from MHBs

## Splitting MHBs into Modules
* pass

## Splitting Modules into content blocks
In order to extract content, goals, ects, etc. from a raw module text, it needs to be splitted into the searched for blocks. <br />
Due to the great variety of different headings for the same semantical meaning (e.g. goals) different techniques have to be used to guarantee an extraction with a high success rate as well as no halluzination. <br />
<br />
To achieve this goal following "game-plan" was developed:

* (optional) Header normalization
    * Based on already extracted data and ai-generated examples and abbreviations different header options will be used to train a semantic NER-Model like BERT
* Header detection
    * Detects headers
* Zero-Shot classification / QA
    * The text between two headers will be split into the first relevant part and the second part, that doesn't fit the semantic meaning of the header and might resemble another block, that wasn't extracted (since it contains irrelevant information or header detection failed; therefore trying to reclassify this block / these blocks might be appropiate)
