# ******** Regulation Miner ******************
# Created by: Alton Leibel
# Created on: 2019-06-01
# Required packages:
#   1. lxml
#   2. beautifulsoup4
#   3. pandas
#   4. requests
#   5. PySimpleGUI
#
# Description:
#   regulation miner will scrape the html of a specified regulation and return a tab separated data
#   file that contains body of the regulation and it's parts while preserving the lineage throughout
#   the data file
#
# Data format:

from bs4 import BeautifulSoup
from collections import OrderedDict
import pandas as pd
import requests
import minerFunctions as udf
import minerGUI as gui


userEntry = gui.prompt_url()
if userEntry[0] == "" or userEntry[1] == "":
    exit()
    print("User input cannot be left blank")
else:
    exportPath = userEntry[1]
    regulationURL = userEntry[0]

# Retrieve regulations html document

# Safe food for Canadians regulations
# "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2018-108/FullText.html"

# Food and drug regulations
# 'https://laws.justice.gc.ca/eng/regulations/c.r.c.,_c._870/FullText.html'

# Migratory birds regulations
# 'https://laws-lois.justice.gc.ca/eng/regulations/C.R.C.,_c._1035/FullText.html'

# Yellowknife Airport zoning regulations *** This doesn't seem to work quite as well, there is loss ***
# 'https://laws-lois.justice.gc.ca/eng/regulations/SOR-81-472/FullText.html'

page = requests.get(regulationURL)

soup = BeautifulSoup(page.content, 'lxml')  # Creates beautiful soup objects

# Drill down to the relevant part of the HTML code
mainBody = soup.find(id='docCont').find('div')  # returns all elements from the page
subPart = mainBody.find_all('section', recursive=False)
intro = subPart[0]  # Stores introduction text
regPart = subPart[1]  # Stores regulation text

# Stores a list heading tag types to take into consideration adn the corresponding level
headingDict = {
    "h2": 1,
    "h3": 2,
    "h4": 3,
    "h5": 4}

# Retrivies title of act or regulation
titleOfAct = soup.find(class_="Title-of-Act").get_text()

# Key value initial assignment
keyFields = OrderedDict([
    ('REGULATION', titleOfAct),
    ('PART', '0'),
    ('DIVISION', '0'),
    ('SUBDIVISION', '0'),
    ('SUBDIVISION CONTEXT', '0'),
    ('SECTION CONTEXT', '0'),
    ('SECTION', '0'),
    ('SUBSECTION CONTEXT', '0'),
    ('SUBSECTION', '0'),
    ('PARAGRAPH', '0'),
    ('SUBPARAGRAPH', '0'),
    ('CLAUSE', '0')
])

# Keeps track of block levels
blockLevel = {
    'REGULATION': 0,
    'PART': 1,
    'DIVISION': 2,
    'SUBDIVISION': 3,
    'SUBDIVISION CONTEXT': 4,
    'SECTION CONTEXT': 5,
    'SECTION': 6,
    'SUBSECTION CONTEXT': 7,
    'SUBSECTION': 8,
    'PARAGRAPH': 9,
    'SUBPARAGRAPH': 10,
    'CLAUSE': 11
}

# Initializes a pandas data frame for heading data
subText = soup.find(class_='ChapterNumber').get_text()
pageData = pd.DataFrame([[0,  # Level
                          "Regulation",  # Type of regulation block
                          titleOfAct,  # Text/number of heading or section
                          titleOfAct,  # Description of heading/caption or section contents
                          '',  # HTML id tag, if any
                          titleOfAct,  # Regulation
                          '0',  # Part
                          '0',  # Division, numeric
                          '0',  # Subdivision, uppercase letter
                          '0',  # Subdivision context, auto-generated number
                          '0',  # Section context, auto-generated number
                          '0',  # Section, number
                          '0',  # Subsection context, auto-generated number
                          '0',  # Subsection, number in brackets (), simplified to show only number
                          '0',  # Paragraph, lower case letter
                          '0',  # Sub paragraph section, roman numeral
                          '0'   # clause section, upper case letter
                          ]]
                        )

# *********** Definitions ********************************
# Retrieves a list of terms and definitions from the regulations.
# These aren't "smart" for now and won't do a very good job at preserving format, however
# The text should be there

definitions = pd.DataFrame([["I am a term", "I am a definition"]])  # initial data frame
for item in soup.find_all('dd'):
    definition = ""
    for string in item.strings:
        if string.parent.name == 'dfn':
            if string.strip() == ")":
                term = "98765"
            else:
                term = string
        else:
            definition = definition + string
    if term == "98765":
        tempDF = pd.DataFrame([[term, definition]])
    else:
        tempDF = pd.DataFrame([[term, term + definition]])

    definitions = definitions.append(tempDF, ignore_index=True)

definitions = definitions.rename(index=str, columns={0: "Term", 1: "Definition"})

# ************ Process regulation bits and pieces *****************
SubdivisionContextCounter = 0
SectionContextCounter = 0
subsectionContextCounter = 0

varList = [9999]
# retrieves body and heading information
for item in regPart.find_all(recursive=False):

    # *************** Process Headings ***********************************
    if item.name in headingDict:
        if item.name == 'h5':
            SubdivisionContextCounter += 1

        varList = udf.proc_heading(item,
                                   headingDict[item.name],
                                   SubdivisionContextCounter)  # Returns cleaned list of data

        # Processes key values
        if varList[1] in keyFields:
            keyFields[varList[1]] = varList[2]  # Stores coded value

            # Reset all codes after the level of the heading
            for i, (key, value) in enumerate(keyFields.items()):
                if i > varList[0]:
                    keyFields[key] = '0'

        #Add key values to list
        for i, (key, value) in enumerate(keyFields.items()):
            varList.append(value)

        # Adds new record to data frame
        pageData = pageData.append(udf.create_dataframe(varList), ignore_index=True)

    # *************** Process tag classes ***********************************
    elif len(item.attrs) > 0:

        # *************** Process marginal notes - Section context  ***********************************
        if item.get('class')[0] == 'MarginalNote':
            SectionContextCounter += 1

            varList = udf.proc_marginalnote(item,
                                             blockLevel['SECTION CONTEXT'],
                                             'SECTION CONTEXT',
                                             SectionContextCounter)

            # Processes key values
            if varList[1] in keyFields:
                keyFields[varList[1]] = varList[2]  # Stores coded value

                # Reset all codes after the level of the heading
                for i, (key, value) in enumerate(keyFields.items()):
                    if i > varList[0]:
                        keyFields[key] = '0'

            # Add key values to list
            for i, (key, value) in enumerate(keyFields.items()):
                varList.append(value)

            # Adds new record to data frame
            pageData = pageData.append(udf.create_dataframe(varList), ignore_index=True)

        # *************** Process Sections ***********************************
        elif item.get('class')[0] == 'Section':
            varList = udf.proc_section(item, blockLevel['SECTION'])

            # Processes key values
            if varList[1] in keyFields:
                keyFields[varList[1]] = varList[2]  # Stores coded value

                # Reset all codes after the level of the heading
                for i, (key, value) in enumerate(keyFields.items()):
                    if i > varList[0]:
                        keyFields[key] = '0'

            # Add key values to list
            for i, (key, value) in enumerate(keyFields.items()):
                varList.append(value)

            # Adds new record to data frame
            pageData = pageData.append(udf.create_dataframe(varList), ignore_index=True)

        # *************** Process provision lists  ***********************************
        elif item.get('class')[0] == 'ProvisionList':
            tempList = udf.proc_provisions(item, subsectionContextCounter)  # Returns a list of page elements

            for varList in tempList:

                if varList[1] == 'SUBSECTION CONTEXT':
                    subsectionContextCounter = int(varList[2])
                # Processes key values
                if varList[1] in keyFields:
                    keyFields[varList[1]] = varList[2]  # Stores coded value

                    # Reset all codes after the level of the heading
                    for i, (key, value) in enumerate(keyFields.items()):
                        if i > varList[0]:
                            keyFields[key] = '0'

                # Add key values to list
                for i, (key, value) in enumerate(keyFields.items()):
                    varList.append(value)

                # Adds new record to data frame
                pageData = pageData.append(udf.create_dataframe(varList), ignore_index=True)


# Force string format on code field
for i in range(16):
    pageData[i] = pageData[i].astype(str)


# Rename pages
pageData = pageData.rename(index=str, columns={0: "level",  # Hierarchial level of the reference regulation block
                                               1: "type",  # Hard coded type of the regulation block ie: [Part, Division, Section, ...]
                                               2: 'reference',  # The number, leter, or text of the regulation block 
                                               3: 'content',  # The text of the block, could be either full sentances or a short description
                                               4: 'html_id',  # The ID attribute, if any, of the html block
                                               5: "regulation",  # the regulation name
                                               6: 'part',  # Part, highest level of a regulation
                                               7: 'division',  # division
                                               8: 'subdivision',  # sub-division
                                               9: 'subdivision_context',  # Explanatory text that provides context to following blocks
                                               10: 'section_context',  # Explanatory text that provides context to following blocks
                                               11: 'section',  # section: this may or may not contain any content if it is with a subsection
                                               12: 'subsection_context',  # Explanatory text that provides context to following blocks
                                               13: 'subsection',  # Sub-section
                                               14: 'paragraph',  # Paragraph
                                               15: 'subparagraph',  # Subparagraph 
                                               16: 'clause'})  # Clause


dataFilePath = exportPath + "/" + titleOfAct.replace(" ", "") + "_data.csv"
definitionFilePath = exportPath + "/" + titleOfAct.replace(" ", "") + "_definitions.csv"

pageData.to_csv(dataFilePath,
                index=False,
                sep='\t',
                quotechar='"',
                header=True,
                quoting=1)

definitions.to_csv(definitionFilePath,
                   index=False,
                   sep='\t',
                   quotechar='"',
                   header=True,
                   quoting=1)
