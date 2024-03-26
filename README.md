
## Installation

To install the required dependencies, run the following command:

`pip install -r requirements.txt`


To run the app, use the following command:

`streamlit run insights.py`


## Files

This project has three main files:

- `insights.py`: This file represents the  main layout for the web app and the logic that glues all the different functionalities together.


## Folders
- components :
  - `database_insights.py` : Contains all of our database-related functionalities
  - `document_QA.py` : Contains our document-interaction functionalities
  - `signal_generation.py` : Contains our Signal generation functionalities
- utils : contains all our utility functions
  - `util_funcs.py`: Contains miscellaneous functions which includes parsing , downloading and zipping etc ...
  - `style.py`: Contains functions that handle style and aesthetics
  - `core_funcs.py`:  Contains all the Langchain functionalities used in the app, like generating the summary , and generating answers for the Q&A
  - `llm_utilities.py` : Contains utility functions that are related to LLMs and the main functionality in general , such as parsing the output , connecting to the SQL chain etc...
  -  
- other : contains 5 subfolders
  - images :
  - prompts :
  - credentials :
  - Cassandra : contains different config files for Cassandra
  - wheels : contains the py wheels files to run Amazon Bedrock
  



