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
llm = OpenAI(temperature=0, verbose=True)
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
As a Microsoft SQL server programmer reading ANSI-SQL, list all the stored procedure names.  Note that procedure names can also have spaces within the name, as long as the name is in quotes.

Output:
procedure_name, procedure_name, procedure_name, ...
"""
    print("Query: ", query)
    ans = qa.run(query)
    print("Answer: ", ans)
    list = ans.split(",")
    return list


# Fetch the procedures
procedures = fetch_procs()

# Output: Not all procedures are found.  Different runs produce different results.
# ['\n"Sales by Year"', ' "CustOrdersDetail"', ' "CustOrdersOrders"', ' "CustOrderHist"', ' "SalesByCategory"', ' "ByRoyalty"', ' "Reptq1"', ' "Reptq2"', ' "Reptq3"']
# ['\n"Sales by Year"', ' "CustOrdersDetail"', ' "CustOrdersOrders"', ' "CustOrderHist"', ' "SalesByCategory"', ' "byroyalty"', ' "reptq1"', ' "reptq2"', ' "reptq3"', ' "Ten Most Expensive Products"', ' "Employee Sales by Country"']
print(procedures)


def fetch_tables_called_by_proc(procedure_name):
    """
    Fetch a list of tables called by a procedure.
    """

    print("Getting Tables for: ", procedure_name)

    prompt = PromptTemplate(
        input_variables=["procedure_name"],
        template="""
            As a Microsoft SQL server programmer reading ANSI-SQL, list all the tables queried or updated by the stored procedure called {procedure_name}.

            Don't list table names unless they occur within the FROM or INTO clauses of a SELECT or UPDATE statement.

            Output:
            table_name, table_name, table_name, ...
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
# Some tables listed are not called by the procedure.
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
As a Microsoft SQL Server syntax parser, find all the CREATE TABLE statements and list all the table names.

Table names can be a single word, or several words that are surrounded by quotes or square brackets.

Example:
CREATE TABLE TableName
Name: TableName

Example:
CREATE TABLE "Table Name"
Name: "Table Name"

Example:
CREATE TABLE "TableName"
Name: TableName

Example:
CREATE TABLE [dbo].[TableName]
Name: TableName

Example:
CREATE TABLE [Table Name]
Name: "Table Name"

Example:
CREATE TABLE [TableName]
Name: TableName


Output:
"TableName", "TableName", "TableName", ...
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
            As a Microsoft SQL server programmer reading ANSI-SQL, list all the tables that have a foreign key foreign key constraint that references the {table_name} table.

            Example:
            CREATE TABLE RelatedTableName (

            CONSTRAINT "FK_Name" FOREIGN KEY 
            (
                "{table_name}ID"
            ) REFERENCES "dbo"."{table_name}" (
                "{table_name}ID"
            )
            )
            GO
            table_name: RelatedTableName

            Example:
            ALTER TABLE RelatedTableName
            ADD CONSTRAINT [FK_Name] FOREIGN KEY 
            (
                [{table_name}ID]
            ) REFERENCES [dbo].[{table_name}] (
                [{table_name}ID]
            )
            GO
            table_name: RelatedTableName

            Output:
            table_name, table_name, table_name, ...
        """,
    )
    query = prompt.format(table_name=table_name)
    ans = qa.run(query)
    print("Query: ", query)
    print("Answer: ", ans)
    list = ans.split(",")
    return list


# Output: Not very accurate at this stage.
# ['\nEmployeeTerritories', ' Orders']
print(fetch_related_tables_for_table("Employees"))
