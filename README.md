# Source Insights Demo App

# Intro

This project uses [langchain](https://python.langchain.com/) on Open AI's GPT models to parse SQL code and create diagrams of candidate service definitions that
could be written to sit over the top of the database layer.  The idea is to facilitate the use of the strangler pattern to write
a layer of services over the database procedures, then to start extracting the procedure logic into the service layer.

The program achieves this by:

1. Parsing the sql code into a pandas dataframe containing all the DDL definitions.
2. Iterating over all the stored procedure code and creating a map of tables that are called by each stored procedure.  The map indicates which tables are queried or updated.
3. Clustering stored procedures together based on their name, the names of the underlying tables and the types of operations performed (READ or WRITE).
4. Creating service definitions from the clustered procedure map.
5. Generating diagrams of the services.

Here's an example of the output:

![](images/Orders.png)

And another one:

![](images/Order_Details.png)

# Findings

The project can successfully find all the stored procedures and the tables that are queried using a GPT-3.5-tubo model.  It uses [scikit-learn](https://scikit-learn.org/stable/) to clusters the procs into
sensible groups using KMeans squared clustering, based on the names of the procs, tables and the operations performed.

The clustering works pretty well and could be easily tuned to desired output.  The interim results are cached in a file called `results/service_candidates_cache.csv` which can be manually tweaked after
initial clustering to get the desired final output.

[PlantUml](https://plantuml.com/) is used to generate the diagrams.

Lessons learned include:

1. You can successfully extract information about key source code with quite simple python programs.  Significantly less complex than language parsing.
2. Short time to implement.  Most of the time was spent learning about AI ;-)
3. Inconsistent results:
    * Not finding ALL source code elements and sometimes see differences between program executions.
    * Variability not improved when "temperature" is set to zero.
    * Sometimes the results aren't formatted correctly either; although these issues could be easily fixed with standard coding techniques, or a second pass through with LLM.
    * The area that was least successful was in extracting all the tables and when trying to find relationships between them by searching for foreign key relationships.
4. You can tune the process to get better results:
    * __LLM Model choice (and token limit)__ - e.g. GPT3 vs 3.5 or 4.  Wasn't able to try GPT-4 yet.
    * __Model "temperature"__ - set to 0 for less randomness in the response.
    * __Input prompts__ - the questions sent to the LLM, e.g.
        * Few shot prompting, i.e. give examples of what you are expecting
        * Being explicit about what the LLM should and shouldn't know e.g. "As a SQL programmer...", this effectively positions your query in the right area of the neural network to get the best results.
        * Asking for multiple completions `-n 3` and comparing or combining the results.
    * __Retrieval Augmented Generation (RAG)__ - Call the LLM multiple times, priming it with content to get better summarisation across the code base.

### What is Retrieval Augmented Generation (RAG)?

![](images/Overview_retrieval_augmented_generation.png)

Credit: [AWS Sagemaker documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/jumpstart-foundation-models-customize-rag.html)

### Key recommendations from Open AI about how to get the most out of GPT

![](images/AI_recommendations.png)

Credit: [Microsoft Build Presentation by Andrej Karpathy](https://www.youtube.com/watch?v=bZQun8Y4L2A)

# Next steps

* Update the readme
* Point this at Azure Open AI
* Tweak it to use Informix code

# Useful references

* [Free Tutorial Series by Samuel Chan](https://www.youtube.com/playlist?list=PLXsFtK46HZxUQERRbOmuGoqbMD-KWLkOS)
* [Neural Network Overview](https://www.youtube.com/watch?v=aIZtJqtzdQs&list=PLMrJAkhIeNNQV7wi9r7Kut8liLFMWQOXn&index=12) - fantastic entry level information about AI and neural networks by Steve Brunton.
* [MS Build - State of GPT](https://www.youtube.com/watch?v=bZQun8Y4L2A) - latest techniques for getting the most out of LLMs.
* [Prompt Engineering Guide](https://www.promptingguide.ai/)
* [Microsoft Open Source Guidance Framework](https://github.com/microsoft/guidance) - template based prompt engineering framework.
* [Llama-Index Index Types](https://gpt-index.readthedocs.io/en/latest/guides/primer/index_guide.html)
* [Next generation AI for developers with the Microsoft Cloud](https://www.youtube.com/watch?v=KMOV1Zy8YeM&list=PLlrxD0HtieHjolPmqWVyk446uLMPWo4oP&index=4&t=2210s) - overview of Azure Open AI
* [Getting started with generative AI using Azure OpenAI Service](https://www.youtube.com/watch?v=o5uhn4GSpQU&list=PLlrxD0HtieHjolPmqWVyk446uLMPWo4oP&index=123) - more detail on Azure Open AI
* [The era of the AI Copilot](https://www.youtube.com/watch?v=FyY0fEO5jVY&list=PLlrxD0HtieHjolPmqWVyk446uLMPWo4oP&index=146) - about Microsoft copilots.
* [Chat with OpenAI CEO and and Co-founder Sam Altman, and Chief Scientist Ilya Sutskever](https://www.youtube.com/watch?v=mC-0XqTAeMQ&t=1s)

# Running the code

For `main.py`, which is based on langchain:

1. Clone the repo
2. Open a terminal in the source directory
3. Call `pipenv install` from the terminal
3. Create a .env file and store your OPENAI_API_KEY in it
4. Call `pipenv run python main.py`

For `llama_demo.py` you can run it with `--create-index` command line switch to build a local vector store index from the content, then you can run is without this switch in subsequent runs to reduce time and cost.  You can also switch between northwind and pubs db code using the `--db <name>` switch.  The index is created locally in JSON format under the ./index directory.

# Testing

This project uses [pytest](https://docs.pytest.org/), run `pipenv run pytest` at the project root to test.  It will pick up test files named `test_*.py` or `*_test.py` in sub-directories.

# Change History

* 0.0.2 - can read pubs db and extract proc names, but doesn't extract associated tables correctly.  Seems to never finish with nwnd database; haven't investigated the cause yet.
* 1.0.0 - first fully working version; works with Open AI, not Azure yet.
