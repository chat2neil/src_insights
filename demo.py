# %%
from dotenv import load_dotenv

from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain import OpenAI
from langchain.prompts import PromptTemplate

load_dotenv()


# %%
# Load the code to analyse
loader = DirectoryLoader("source_code/sql_server", glob="**/*.sql", loader_cls=TextLoader, show_progress=True)
documents = loader.load()
documents

# %%
splitter = RecursiveCharacterTextSplitter(separators=["GO\n", "\n\n", "\n"], chunk_size=2500, chunk_overlap=0)
chunks = splitter.split_documents(documents)
chunks

# %%
embeddings = OpenAIEmbeddings()
docsearch = Chroma.from_documents(chunks, embeddings)


# %%
llm = OpenAI(verbose=True)

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=docsearch.as_retriever()
)


# %%
def fetch_procs():
    query = """
As a Microsoft SQL server programmer reading ANSI-SQL, list all the stored procedure names.  Note that procedure names can also have spaces within the name, as long as the name is in quotes.

Output:
procedure_name, procedure_name, procedure_name, ...
"""
    print("Query: ", query)
    ans = qa.run(query)
    print("Answer: ", ans)
    list = ans.split(',')
    return list


# %%
procedures = fetch_procs()
procedures

# %%


# %%
for proc in procedures:
    print(proc)

# %%

def fetch_tables_called_by_proc(procedure_name):
    print("Getting Tables for: ", procedure_name)

    prompt = PromptTemplate(
        input_variables=["procedure_name"],
        template="""
            As a Microsoft SQL server programmer reading ANSI-SQL, list all the tables queried or updated by the stored procedure called {procedure_name}.

            Don't list table names unless they occur within the FROM or INTO clauses of a SELECT or UPDATE statement.

            Output:
            table_name, table_name, table_name, ...
        """
    )
    query = prompt.format(procedure_name=procedure_name)
    ans = qa.run(query)
    print("Query: ", query)
    print("Answer: ", ans)
    list = ans.split(',')
    return list

# %%
print(fetch_tables_called_by_proc("proc"))

# %%

tables_by_procedure_struct = {}
for proc in procedures:
    tables_by_procedure_struct[proc] = fetch_tables_called_by_proc(proc)



# %%
tables_by_procedure_struct

# %%
def fetch_tables():
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
    list = ans.split(',')
    return list

# %%
tables = fetch_tables()
tables

# %%
def fetch_foreign_keys_for_table(table_name):
    print("Getting FKs for Table: ", table_name)

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
        """
    )
    query = prompt.format(table_name=table_name)
    ans = qa.run(query)
    print("Query: ", query)
    print("Answer: ", ans)
    list = ans.split(',')
    return list

# %%
print(fetch_foreign_keys_for_table("Employees"))

# %%



