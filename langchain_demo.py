from dotenv import load_dotenv
from langchain import HuggingFaceHub, LLMChain, OpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

llm = HuggingFaceHub(repo_id="openlm-research/open_llama_13b")

prompt = PromptTemplate(
    input_variables=["question"],
    template= """
    In polite and simple terms, my response to {question} is ...
    """
)

llm = LLMChain(llm=llm, prompt=prompt, verbose=True)

def create_query(llm, question):
    print(f"Question: {question}")
    print(f"Answer: {llm.run(question)}\n\n")

create_query(llm, "how many major cities are there in the world?")
create_query(llm, "calculate the total sales by month, product category and region")
create_query(llm, "list the top 50 products that have fewer than 100 units in stock")

