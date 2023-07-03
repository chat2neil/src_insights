# Source Insights Demo App

Uses AI frameworks such as [llama-index](https://gpt-index.readthedocs.io/en/latest/guides/primer/usage_pattern.html) and [langchain](https://python.langchain.com/) to try and extract useful information from SQL code to speed up analysis and design.

# Getting started

1. Clone the repo
2. Open a terminal in the source directory
3. Call `pipenv install` from the terminal
3. Create a .env file and store your OPENAI_API_KEY in it
4. Call `pipenv run python main.py --create-index` for first run, this reads the SQL source and generates the index
5. Call `pipenv run python main.py` for subsequent executions, this loads the index and runs the queries based on the data already stored in the index.

The index is created locally in JSON format under the ./index directory.

Note that you can add `--db nwnd` `--db pubs` when creating the index to between input database code files.  The default is pubs.  The nwnd one takes a while to build.

# Change History

* 0.0.2 - can read pubs db and extract proc names, but doesn't extract associated tables correctly.  Seems to never finish with nwnd database; haven't investigated the cause yet.
