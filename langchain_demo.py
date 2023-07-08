from dotenv import load_dotenv

from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain import OpenAI

load_dotenv()

# Load the code to analyse
loader = DirectoryLoader("source_code/sql_server", glob="**/*.sql", loader_cls=TextLoader, show_progress=True)
documents = loader.load()
# print(len(documents))

# Split the code into chunks
splitter = RecursiveCharacterTextSplitter(separators=["GO\n", "\n\n", "\n"], chunk_size=2500, chunk_overlap=0)
chunks = splitter.split_documents(documents)
# print(chunks)

embeddings = OpenAIEmbeddings()
docsearch = Chroma.from_documents(chunks, embeddings)

llm = OpenAI(verbose=True)

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=docsearch.as_retriever()
)

def query(q):
    print("Query: ", q)
    print("Answer: ", qa.run(q))

query("""
As a Microsoft SQL server programmer reading ANSI-SQL, list all the stored procedure names.  Note that procedure names can also have spaces within the name, as long as the name is in quotes.

Output:
procedure_name, procedure_name, procedure_name, ...
""")
# query("As a Microsoft SQL server programmer reading ANSI-SQL, list all the stored procedure names")
# query("As a SQL server programmer, list all the stored procedure names and the tables that they query")
# query("As a SQL server programmer, list all the stored procedure names and the tables that they query")
