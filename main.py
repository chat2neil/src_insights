from dotenv import load_dotenv
import argparse
import pandas as pd
import re
import json
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from jinja2 import Template
import subprocess

load_dotenv()


def find_database_objects_in_code(sql_code):
    """
    Find all the Data Definition Language (DDL) statements in the SQL CODE provided and extract the statement type and the name of the database object being created, altered or dropped.
    """

    chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, verbose=True)
    system_message_prompt = SystemMessagePromptTemplate.from_template("""
        Your are a SQL code parser.

        Find all the Data Definition Language (DDL) statements in the SQL CODE provided and extract the statement type and the name of the database object being created, altered or dropped.

        ## OUTPUT FORMAT ##
        json object array, containing the name of the database object and the DDL statement type in UPPERCASE text.
        Example:
        [{{ "db_object_name": "EmployeeID", "dml_operation": "CREATE INDEX"}}]

        If there are no items, then return an empty json array.
    """)
    example1_prompt = HumanMessagePromptTemplate.from_template('CREATE TABLE "Products"')
    example1_response = AIMessagePromptTemplate.from_template('[{{ "db_object_name": "Products", "dml_operation": "CREATE TABLE"}}]')

    example2_prompt = HumanMessagePromptTemplate.from_template('CONSTRAINT "FK_Products_Categories" FOREIGN KEY')
    example2_response = AIMessagePromptTemplate.from_template('[{{ "db_object_name": "FK_Products_Categories", "dml_operation": "CREATE CONSTRAINT"}}]')

    example3_prompt = HumanMessagePromptTemplate.from_template('create procedure "Sales by Year"')
    example3_response = AIMessagePromptTemplate.from_template('[{{ "db_object_name": "Sales by Year", "dml_operation": "CREATE PROCEDURE"}}]')

    example4_prompt = HumanMessagePromptTemplate.from_template("""
    if exists (select * from sysobjects where id = object_id('dbo.Employee Sales by Country') and sysstat & 0xf = 4)
	    drop procedure "dbo"."Employee Sales by Country"
    GO
    """)
    example4_response = AIMessagePromptTemplate.from_template('[{{ "db_object_name": "Employee Sales by Country", "dml_operation": "DROP PROCEDURE"}}]')

    example5_prompt = HumanMessagePromptTemplate.from_template("""
    if exists (select * from sysobjects where id = object_id('dbo.Category Sales for 1997') and sysstat & 0xf = 2)
	    drop view "dbo"."Category Sales for 1997"
    GO
    """)
    example5_response = AIMessagePromptTemplate.from_template('[{{ "db_object_name": "Category Sales for 1997", "dml_operation": "DROP VIEW"}}]')

    final_prompt = HumanMessagePromptTemplate.from_template("""
    ## CODE ##
    {sql_code_fragment}

    Output:
    """)
    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt, 
        example1_prompt, example1_response,
        example2_prompt, example2_response,
        example3_prompt, example3_response,
        example4_prompt, example4_response,
        example5_prompt, example5_response,
        final_prompt
    ])

    # get a chat completion from the formatted messages
    llm_response = chat(chat_prompt.format_prompt(sql_code_fragment=sql_code).to_messages())
    result = json.loads(llm_response.content)
    return result


def load_sql_and_parse_into_ddl_statements_dataframe(source_directory, source_file_glob_pattern="**/*.sql"):
    """
    Load the SQL DDL statements from the file and categorise them into the following types:
    - CREATE TABLE
    - CREATE INDEX
    - CREATE PROCEDURE
    - CREATE VIEW
    - CREATE CONSTRAINT
    - ALTER TABLE
    - ALTER INDEX
    - ALTER PROCEDURE
    - ALTER VIEW
    - ALTER CONSTRAINT
    - DROP TABLE
    - DROP INDEX
    - DROP PROCEDURE
    - DROP VIEW
    - DROP CONSTRAINT
    """

    # Load the code to analyse
    loader = DirectoryLoader(
        source_directory, glob=source_file_glob_pattern, loader_cls=TextLoader, show_progress=True
    )
    documents = loader.load()

    # Split the code into chunks, ideally where there is a GO statement which indicates the end of a significant code block.
    splitter = RecursiveCharacterTextSplitter(
        separators=["GO\n", "go\n", "\n\n", "\n"], chunk_size=2000, chunk_overlap=0, keep_separator=True
    )
    chunks = splitter.split_documents(documents)
    sample_chunks = chunks #chunks[0:20]

    ddl_statements_dataframe = pd.DataFrame(columns=['db_object_name', 'dml_operation', 'sql_code'])
    for chunk in sample_chunks:
        content = chunk.page_content
        database_objects = find_database_objects_in_code(content)
        temp_df = pd.DataFrame(database_objects)
        temp_df['sql_code'] = content
        ddl_statements_dataframe = pd.concat([ddl_statements_dataframe, temp_df], ignore_index=True)

    return ddl_statements_dataframe


def list_procedure_names(source_insights_dataframe):
    """
    Find all the procedure names in the source insights data frame.
    """
    procedures = source_insights_dataframe[source_insights_dataframe['dml_operation'] == 'CREATE PROCEDURE']
    return procedures['db_object_name'].to_list()


def list_table_names(source_insights_dataframe):
    """
    Find all the table names in the source insights data frame.
    """
    tables = source_insights_dataframe[source_insights_dataframe['dml_operation'] == 'CREATE TABLE']
    return tables['db_object_name'].to_list()


def extract_procedure_declaration_from_code(procedure_name, sql_code):
    """
    Extract the procedure declaration from the SQL code.
    
    Uses a regular expression to fetch the code between the CREATE PROCEDURE 
    statement and the GO statement.
    """
    regex_pattern = r'(CREATE PROCEDURE +?"?%s"?.+?(\nGO|$))' % procedure_name
    match = re.search(regex_pattern, sql_code, re.DOTALL | re.IGNORECASE)
    if match:
        procedure_code = match.group(1)
    else:
        procedure_code = None
    return procedure_code


def find_tables_manipulated_by_procedure(procedure_name, sql_code):
    """
    Find all the database tables that are manipulated by the procedure.

    Returns a list of dictionaries containing the name of the table and the 
    DML statement type (i.e. SELECT, INSERT, UPDATE, or DELETE).

    Example:
    [
        { "table_name": "Order Details", "dml_operation": "SELECT"},
        { "table_name": "Order Details", "dml_operation": "INSERT"},
        { "table_name": "Order Details", "dml_operation": "UPDATE"},
        { "table_name": "Order Details", "dml_operation": "DELETE"},
    ]
    """
    chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, verbose=True)
    system_message_prompt = SystemMessagePromptTemplate.from_template("""
        Your are a SQL code parser.

        Find all the database tables that are manipulated by the {procedure_name} stored procedure.
        Find all the tables that are queried, inserted into, updated or deleted from and extract the 
        table name and database operation type (i.e. SELECT, INSERT, UPDATE, or DELETE).

        ## OUTPUT FORMAT ##
        json object array, containing the name of the table and the DML statement type in UPPERCASE text.
        Example:
        [{{ "table_name": "Order Details", "dml_operation": "SELECT"}}]

        If there are no items, then return an empty json array.
    """)
    example1_prompt = HumanMessagePromptTemplate.from_template("""
    CREATE PROCEDURE CustOrdersDetail @OrderID int
    AS
    SELECT ProductName,
        UnitPrice=ROUND(Od.UnitPrice, 2),
        Quantity,
        Discount=CONVERT(int, Discount * 100), 
        ExtendedPrice=ROUND(CONVERT(money, Quantity * (1 - Discount) * Od.UnitPrice), 2)
    FROM Products P, [Order Details] Od
    WHERE Od.ProductID = P.ProductID and Od.OrderID = @OrderID
    go
    """)
    example1_response = AIMessagePromptTemplate.from_template('[{{ "table_name": "Products", "dml_operation": "SELECT"}}, {{ "table_name": "Order Details", "dml_operation": "SELECT"}}]')

    example2_prompt = HumanMessagePromptTemplate.from_template("""
    CREATE PROCEDURE CustOrdersOrders @CustomerID nchar(5)
    AS
    SELECT OrderID, 
        OrderDate,
        RequiredDate,
        ShippedDate
    FROM Orders
    WHERE CustomerID = @CustomerID
    ORDER BY OrderID
    GO
    """)
    example2_response = AIMessagePromptTemplate.from_template('[{{ "table_name": "Orders", "dml_operation": "SELECT"}}]')

    final_prompt = HumanMessagePromptTemplate.from_template("{sql_code_fragment}")

    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt, 
        example1_prompt, example1_response,
        example2_prompt, example2_response,
        final_prompt
    ])

    # get a chat completion from the formatted messages
    llm_response = chat(chat_prompt.format_prompt(procedure_name=procedure_name, sql_code_fragment=sql_code).to_messages())
    result = json.loads(llm_response.content)
    return result


def group_tables_by_dml_operation(array_of_table_names_and_dml_operations):
    """
    Given an array of dictionaries, group the dictionaries by the dml_operation key
    and return a dictionary with the dml_operation as the key and the table_name as the value.

    Example:
    Input: [{'table_name': 'Orders', 'dml_operation': 'SELECT'}, {'table_name': 'Order Subtotals', 'dml_operation': 'SELECT'}]
    Output: {'SELECT': 'Orders, Order Subtotals'}
    """
    dict_by_operation = {}

    # Iterate over the array
    for item in array_of_table_names_and_dml_operations:
        # If the dml_operation is not in the dictionary, add it with the table_name as the value
        if item['dml_operation'] not in dict_by_operation:
            dict_by_operation[item['dml_operation']] = item['table_name']
        # If the dml_operation is already in the dictionary, append the table_name to the existing value
        else:
            dict_by_operation[item['dml_operation']] += ', ' + item['table_name']
    return dict_by_operation


def cluster_procedures_by_table_and_operation(df, number_of_clusters=5):
    """
    Cluster the procedures by the tables that they operate on and the operation type.

    This function adds a cluster_label and a combined_feature column to the DataFrame.
    """

    # Step 1: Define the features that you want to use to cluster the records
    # Combine 'table_name' and 'procedure_name' into a single feature
    df['combined_feature'] = df['table_name'] + ' ' + df['procedure_name'] + ' ' + df['operation_type']

    # Convert the 'combined_feature' column to a matrix of TF-IDF features
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df['combined_feature'])

    # Step 2: Use a clustering algorithm to cluster the records based on these features
    # Let's use KMeans as an example
    kmeans = KMeans(n_clusters=number_of_clusters)
    kmeans.fit(X)

    # Assign the cluster labels to the records
    df['cluster_label'] = kmeans.labels_
    return df


def derive_service_name(group):
    """
    Derive the service name for a group of rows, containing the table_name and operation_type columns.

    The service name is derived from the most common table name in the group, where the operation_type is WRITE.
    If there are no WRITE operations, then the service name is derived from the most common table name in the group.
    If there are no rows in the group, then the service name is set to 'Service With No Name'.
    """

    # Prefer to name service according to which tables they write to, if possible
    group_write = group[group['operation_type'] == 'WRITE']

    if group_write.empty:
        if group.size > 0:
            most_common_table = group['table_name'].value_counts().idxmax()
            return most_common_table
        else:
            return 'Service With No Name'

    most_common_table = group_write['table_name'].value_counts().idxmax()
    return most_common_table


def add_derived_service_name_for_each_cluster_based_on_most_common_table_name(df):
    """
    Derive the service name for each cluster, based on the most common table name in the cluster.

    This function adds a service_name column to the DataFrame.
    """

    # Derive the service name for each cluster, pass the table_name and operation_type columns 
    # to the derive_service_name function.  Assign the service names to a new column called service_name.
    service_names = df.groupby('cluster_label')[['table_name', 'operation_type']].apply(derive_service_name).reset_index()
    service_names.columns = ['cluster_label', 'service_name']

    # Merge the service names into the original DataFrame
    df = pd.merge(df, service_names, on='cluster_label')

    return df


def replace_spaces_with_underscores_in_names(df):
    """
    Replace spaces with underscores in the service_name, table_name and procedure_name columns
    """
    for col in ['service_name', 'procedure_name', 'table_name']:
        df[col] = df[col].str.replace(' ', '_')
    return df


def create_service_diagram(service_name, procedures, read_tables, write_tables):
  """
  Given a service name, procedures, read tables, and write tables, create a PlantUML diagram.
  """    
  diagram_template_text = """
  @startuml "{{ service_name }}"

  class {{ service_name }} <<domain service>> {
    {%- for procedure in procedures %}
    + {{ procedure }}() <<api>>
    {%- endfor %}
  }

  package "{{ service_name }}_PROCS" {
    {% for procedure in procedures %}
    class {{ procedure }} <<proc>> {
    }
    {% endfor %}
  }

  package "{{ service_name }}_READS" {
    {% for table in read_tables %}
    class {{ table }} <<table>> {
    }
    {% endfor %}
  }

  package "{{ service_name }}_WRITES" {
    {% for table in write_tables %}
    class {{ table }} <<table>> {
    }
    {% endfor %}
  }

  {{ service_name }} --> "{{ service_name }}_PROCS" : calls
  {{ service_name }}_PROCS --> "{{ service_name }}_READS" : reads
  {{ service_name }}_PROCS --> "{{ service_name }}_WRITES" : writes

  @enduml
  """

  template = Template(diagram_template_text)
  rendered_text = template.render(service_name=service_name, procedures=procedures, read_tables=read_tables, write_tables=write_tables)
  # print(rendered_text)

  diagram_path = f"./results/{service_name}.puml"
  with open(diagram_path, 'w') as file:
        file.write(rendered_text)

  cmd = f'plantuml {diagram_path}'
  subprocess.run(cmd, shell=True, check=True)



def create_service_diagrams(df):
    """
    Create a PlantUML diagram for each service.

    The diagram will show the procedures, read tables, and write tables for each service.
    """
    for service_name in df['service_name'].unique():
        procedures = df[df['service_name'] == service_name]['procedure_name'].unique()
        read_tables = df[(df['service_name'] == service_name) & (df['operation_type'] == 'READ')]['table_name'].unique()
        write_tables = df[(df['service_name'] == service_name) & (df['operation_type'] == 'WRITE')]['table_name'].unique()
        create_service_diagram(service_name, procedures, read_tables, write_tables)


# ------------------------------------------------------------
# Main program
# ------------------------------------------------------------

# Parse the command line arguments
parser = argparse.ArgumentParser(description='Source insigts for SQL code')
parser.add_argument('--parse-code',
                    type=bool,
                    default=False,
                    help='set to true to parse the original SQL code, if false, then use the results from the previous run are used')
args = parser.parse_args()

if args.parse_code:
    source_insights_dataframe = load_sql_and_parse_into_ddl_statements_dataframe("source_code/sql_server", source_file_glob_pattern="**/*.sql")
    source_insights_dataframe.to_csv('./results/sql_src_insights.csv', index=False)
else:
    source_insights_dataframe = pd.read_csv('./results/sql_src_insights.csv')

procedure_names = list_procedure_names(source_insights_dataframe)
print("Found procedures:")
print(procedure_names)

table_names = list_table_names(source_insights_dataframe)
print("Found tables:")
print(table_names)

print("Done.")
