# import os
import argparse
from dotenv import load_dotenv
from llama_index import SimpleDirectoryReader, load_index_from_storage, StorageContext
from llama_index.node_parser import SimpleNodeParser
from llama_index import VectorStoreIndex

# Load environment variables from .env file
# NOTE: This will read in the OPENAI_API_KEY into the os.environ dictionary
# This key is used by the OpenAI API to authenticate requests
load_dotenv()


def create_index(db_name):
    print("Creating index from source code")
    documents = SimpleDirectoryReader(
        input_files=[f"source_code/sql_server/inst{db_name}.sql"]
    ).load_data()
    # print(documents)

    nodeParser = SimpleNodeParser()
    nodes = nodeParser.get_nodes_from_documents(documents)
    # print(nodes)

    # index = VectorStoreIndex.from_documents(documents)
    index = VectorStoreIndex(nodes)
    index.storage_context.persist(persist_dir="./index")
    return index


def load_index():
    print("Loading index from disk")
    storage_context = StorageContext.from_defaults(persist_dir="./index")
    index = load_index_from_storage(storage_context)
    return index


def get_stored_procedures(index):
    query_engine = index.as_query_engine()
    response = query_engine.query(
        """
    Look through the SQL code and find all the stored procedures.

    Procedures are defined as a block of code that starts with the keywords "CREATE" and "PROCEDURE" ends with the keyword "GO".

    The keywords are case insensitive.
    
    The procedure name is the first word or quoted string after the keyword "PROCEDURE".

    Example:
    create procedure "Ten Most Expensive Products" AS
    ...
    GO
    is a procedure named "Ten Most Expensive Products"

    Example:
    CREATE PROCEDURE "Employee Sales by Country" AS
    ...
    GO
    is a procedure named "Employee Sales by Country"

    Example:
    CREATE PROCEDURE CustOrdersDetail @OrderID int
    AS
    ...
    go
    is a procedure named CustOrdersDetail

    Example:
    CREATE PROCEDURE CustOrdersOrders @CustomerID nchar(5)
    AS
    ...
    GO
    is a procedure named CustOrdersOrders

    Please list the procedure names in a comma separated list.  Provide an empty string if no procedures are found.:
    procedure1, procedure2, procedure3
    """
    )

    # Split response by comma and trim whitespace of each element
    name_list = response.response
    stored_procedure_names = [x.strip() for x in name_list.split(",")]
    return stored_procedure_names


def get_tables_accessed_by_procedure(index, procedure_name):
    query_engine = index.as_query_engine()
    response = query_engine.query(
        f"""
        As a sql programmer, given the procedure name {procedure_name}, I want to know what tables are accessed by the procedure.

        To do this analyse the SQL code that sits between the CREATE PROCEDURE, AS and GO keywords.

        Keywords are case insensitive.

        Example:
        CREATE PROCEDURE "Ten Most Expensive Products" AS
            SELECT TOP 10 UnitPrice, ProductName
            FROM Products
            ORDER BY UnitPrice DESC;
        GO
        is a procedure named "Ten Most Expensive Products" that accesses the table "Products"
        return "Products"

        Example:
        CREATE PROCEDURE CustOrdersOrders @CustomerID nchar(5)
        AS
            SELECT Orders.*, [Order Details].*
            FROM Orders
            INNER JOIN [Order Details] ON Orders.OrderID = [Order Details].OrderID
            WHERE Orders.CustomerID = @CustomerID;
        GO
        is a procedure named CustOrdersOrders that accesses the tables Orders and Order Details
        return "Orders, Order Details"

        Example if tables are found:
        table1, table2, table3

        Return an empty string if no tables are found.
        """
    )

    # Split response by comma and trim whitespace of each element
    table_list = response.response
    table_names = [x.strip() for x in table_list.split(",")]
    return table_names


def assert_correct_tables_found(procedure_name, actual_table_names, expected_table_names):
    """
        Assert that the tables found match those expected.
    """
    try:
        assert ",".join(actual_table_names) == ",".join(expected_table_names)
    except:
        print(
            f"{procedure_name} procedure doesn't have expected tables\r\nExpected: {expected_table_names}\r\nActual: {actual_table_names}\r\n"
        )
        raise



# Parse command line args
argParser = argparse.ArgumentParser()
argParser.add_argument(
    "--db",
    help="Specify which database to use, either nwnd or pubs",
    default="pubs",
)
argParser.add_argument(
    "--create-index", action="store_true", help="Create the index"
)
args = argParser.parse_args()

db_name = args.db

# Read command line argument --create_index to determine if we should create the index
if args.create_index:
    index = create_index(db_name)
else:
    index = load_index()

stored_procedure_names = get_stored_procedures(index)
print(f"Procedures: {stored_procedure_names}")

results = {}
for procedure_name in stored_procedure_names:
    table_names = get_tables_accessed_by_procedure(index, procedure_name)
    results[procedure_name] = table_names
    print(f"-------------\r\nProcedure: {procedure_name}\r\nTables: {table_names}")

# Write assertion tests here
# Expect to see the following tables accessed by the procedure "Employee Sales by Country"
# assert results.keys.length == 8
# assert results['CustOrdersOrders'] == "Orders, [Order Details]"
# assert results['CustOrdersDetail'] == "Orders, [Order Details], Products"
# assert results['Employee Sales by Country'].__repr__ == "Employees, Orders, Order Subtotals"
assert_correct_tables_found(
    "Employee Sales by Country", results['"Employee Sales by Country"'], ["Employees", "Orders", "Order Subtotals"]
)
# assert results['Sales by Year'] == "Orders, [Order Details]"
# assert results['Sales by Category'] == "Products, [Order Details], Categories"
# assert results['Ten Most Expensive Products'] == "Products"

print("SUCCESS!")
