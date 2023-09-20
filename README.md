
## Installation

To install the required dependencies, run the following command:

`pip install -r requirements.txt`


To run the app, use the following command:

`streamlit run insights.py`


## Files

This project has three main files:

- `insights.py`: This file contains the main layout for the web app and the logic that glues all the different functionalities together.
- `util_funcs.py`: This file contains miscellaneous functions which includes parsing , downloading and zipping etc ...
- `style.py`: This file has functions that handle style and aesthetics
- `core_funcs.py`: This file contains all the Langchain functionalities used in the app, like generating the summary , and generating answers for the Q&A
- `llm_utilities.py` : This file contains utility functions that are related to LLMs and the main functionality in general , such as parsing the output , connecting to the SQL chain etc...

## Folders
- Cassandra : this folder contains different config files for Cassandra
- other : contains 3 subfolders
  - images
  - prompts
  - credentials
- wheels : contains the py wheels files to run Amazon Bedrock



