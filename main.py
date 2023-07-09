from dotenv import load_dotenv

from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain import OpenAI
from langchain.prompts import PromptTemplate


# This is a langchain implementation, aiming to parse SQL Server code and ouput lists of procedures, tables and dependencies.

load_dotenv()

# Load the code to analyse
loader = DirectoryLoader(
    "source_code/sql_server", glob="**/*.sql", loader_cls=TextLoader, show_progress=True
)
documents = loader.load()
# print(len(documents))

# Split the code into chunks, ideally where there is a GO statement which indicates the end of a significant code block.
splitter = RecursiveCharacterTextSplitter(
    separators=["GO\n", "\n\n", "\n"], chunk_size=2500, chunk_overlap=0
)
chunks = splitter.split_documents(documents)
# print(chunks)

# Create a vector store index from the chunks
embeddings = OpenAIEmbeddings()
docsearch = Chroma.from_documents(chunks, embeddings)

# Pick an LLM model to use
# llm = OpenAI(model_name='text-davinci-003', max_tokens=800, temperature=0, verbose=True)
# llm = OpenAI(model_name='gpt-3.5-turbo', max_tokens=3900, temperature=0, verbose=True)
llm = OpenAI(model_name='gpt-3.5-turbo-16k', max_tokens=8000, temperature=0, verbose=True)
# llm = OpenAI(model="ada", temperature=0, max_tokens=2049, verbose=True)
# llm = OpenAI(model="text-davinci-003", temperature=0, verbose=True)
# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, verbose=True)

# Configure a QA chain, use stuffing to prime the LLM with the question and the results from the vector store retrieval.
qa = RetrievalQA.from_chain_type(
    llm=llm, chain_type="stuff", retriever=docsearch.as_retriever()
)


def fetch_procs():
    """
    Fetch a list of procedures from the SQL Server code.
    """
    query = """
    As a SQL programmer, list the stored procedure names; which can be one word, or multiple words in quotes or square brackets.
    
    Output format:
    procedure_name, procedure_name, ...
    """
    print("Query: ", query)
    ans = qa.run(query)
    print("Answer: ", ans)
    list = ans.split(",")
    return list


# Fetch the procedures
procedures = fetch_procs()

# Output: Not all procedures are found.  Different runs produce different results.
# ['"Sales by Year"', ' CustOrdersDetail', ' CustOrdersOrders', ' CustOrderHist', ' SalesByCategory', ' byroyalty', ' reptq1', ' reptq2', ' reptq3', ' "Ten Most Expensive Products"', ' "Employee Sales by Country"']
print(procedures)


def fetch_tables_called_by_proc(procedure_name):
    """
    Fetch a list of tables called by a procedure.
    """

    print("Getting Tables for: ", procedure_name)

    prompt = PromptTemplate(
        input_variables=["procedure_name"],
        template="""
            As a SQL programmer, list all the tables queried or updated by the stored procedure called {procedure_name}.

            Don't list table names unless they occur within the FROM or INTO clauses of a SELECT or UPDATE statement.

            Output format:
            table_name, table_name, ...
        """,
    )
    query = prompt.format(procedure_name=procedure_name)
    ans = qa.run(query)
    print("Query: ", query)
    print("Answer: ", ans)
    list = ans.split(",")
    return list


# Fetch the tables called by each procedure
tables_by_procedure_struct = {}
for proc in procedures:
    tables_by_procedure_struct[proc] = fetch_tables_called_by_proc(proc)


# Output: This output is pretty useful, but not perfect.
# The output format is inconsistent, but could be tidied up.
# 
# Output from gpt-3.5-turbo-16k: (all correct except reptq3)
# {
#   '"Sales by Year"': ['Orders', ' "Order Subtotals"'], 
#   ' CustOrdersDetail': ['"Products"', ' "[Order Details]"'], 
#   ' CustOrdersOrders': ['Orders'], 
#   ' CustOrderHist': ['The tables queried by the stored procedure CustOrderHist are:\n- Products\n- [Order Details]\n- Orders\n- Customers'], 
#   ' SalesByCategory': ['Categories', ' Products', ' Orders', ' [Order Details]'], 
#   ' byroyalty': ['titleauthor'], 
#   ' reptq1': ['The stored procedure "reptq1" queries the "titles" table.'], 
#   ' reptq2': ['The stored procedure "reptq2" queries the "titles" table.'], 
#   ' reptq3': ['titleauthor', ' titles'], 
#   ' "Ten Most Expensive Products"': ['Products'], 
#   ' "Employee Sales by Country"': ['Orders', ' "Order Subtotals"', ' Employees']
# }
# 
# Output from text-davinci-003:
# {
#   '\n"Sales by Year"': [' Orders', ' "Order Subtotals"', ' "Order Details Extended"'],
#   ' "CustOrdersDetail"': [' Products', ' Order Details'],
#   ' "CustOrdersOrders"': [' Orders', ' Customers'],
#   ' "CustOrderHist"': [' Customers', ' Order Details', ' Orders', ' Products'],
#   ' "SalesByCategory"': [' [Order Details]', ' [Orders]', ' Products', ' Categories'],
#   ' "byroyalty"': [' titleauthor'],
#   ' "reptq1"': [' titles'],
#   ' "reptq2"': [' titles'],
#   ' "reptq3"': [' titles', ' titleauthor', ' roysched'],
#   ' "Ten Most Expensive Products"': [' Products'],
#   ' "Employee Sales by Country"': [' Employees', ' Orders', ' Order Subtotals']
# }
print(tables_by_procedure_struct)


def fetch_all_tables():
    """
    Fetch a list of all tables in the SQL Server code.
    """
    query = """
As a SQL programmer, list the the table names, which can be one word, or multiple words in quotes or square brackets.

Output format:
TableName, TableName, ...
"""
    print("Query: ", query)
    ans = qa.run(query)
    print("Answer: ", ans)
    list = ans.split(",")
    return list


tables = fetch_all_tables()

# Output: Output is pretty good, but not perfect.
# Lists views as well as tables.  When I tried to eliminate the views, the number
# of legitimate tables was reduced.
# 
# Output from gpt-3.5-turbo-16k:
# ['"dbo"."Order Details"', ' Customers', ' Suppliers', ' Products', ' Categories', ' Orders', 
# ' "Product Sales for 1997"', ' titles', ' titleauthor', ' roysched', ' authors', ' publishers', 
# ' employee', ' jobs', ' pub_info', ' sales', ' stores', ' discounts']
# 
# Output from text-davinci-003:
# ['\nShippers', ' Suppliers', ' EmployeeTerritories', ' Territories', ' Region', ' Employees',
# ' Categories', ' Customers', ' Alphabetical list of products', ' Current Product List',
# ' Orders Qry', ' Products Above Average Price', ' Products by Category', ' Quarterly Orders']
print(tables)


def fetch_related_tables_for_table(table_name):
    """
    Fetch a list of tables that refer to a particular table.
    """
    print("Getting related tables for table: ", table_name)

    prompt = PromptTemplate(
        input_variables=["table_name"],
        template="""
        As a SQL programmer, list all foreign key constraints that reference the {table_name} table.

        Output format:
        table_name, table_name, ...
        """,
    )
    query = prompt.format(table_name=table_name)
    ans = qa.run(query)
    print("Query: ", query)
    print("Answer: ", ans)
    list = ans.split(",")
    return list


# Outputs: ['EmployeeTerritories', ' Employees'], but doesn't find Orders
print(fetch_related_tables_for_table("Employees"))

# Outputs: ['Employees', ' Suppliers', ' Orders'], but should only be Products
print(fetch_related_tables_for_table("Suppliers"))

# Outputs: ['EmployeeTerritories', ' Territories'], but should only be Territories
print(fetch_related_tables_for_table("Region"))
