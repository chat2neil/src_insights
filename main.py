
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
    documents = SimpleDirectoryReader(input_files=[f'source_code/sql_server/inst{db_name}.sql']).load_data()
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
    response = query_engine.query("""
    As a sql programmer, I want to know all the names of the stored procedures.
    Example:
    procedure1, procedure2, procedure3
    """)

    # Split response by comma and trim whitespace of each element
    name_list = response.response
    stored_procedure_names = [x.strip() for x in name_list.split(',')]
    return stored_procedure_names
    

if __name__ == "__main__":
    # Parse command line args
    argParser = argparse.ArgumentParser()
    argParser.add_argument('--db', help='Specify which database to use, either nwnd or pubs', default='pubs')
    argParser.add_argument('--create-index', action='store_true', help='Create the index')
    args = argParser.parse_args()

    db_name = args.db

    # Read command line argument --create_index to determine if we should create the index
    if args.create_index:
        index = create_index(db_name)
    else:
        index = load_index()
    
    stored_procedure_names = get_stored_procedures(index)
    print(f"Found procedures: {stored_procedure_names}")

    for procedure_name in stored_procedure_names:
        print(f"Procedure: {procedure_name}")
        query_engine = index.as_query_engine()
        response = query_engine.query(f"""
        As a sql programmer, I want to know what tables are queried, inserted into, updated, or deleted from by the stored procedure {procedure_name}.  Please list the tables in a comma separated list.  Provide an empty string if no tables are queried, inserted into, updated, or deleted from.
        Example if tables are found:
        table1, table2, table3
        """)

        # Split response by comma and trim whitespace of each element
        table_list = response.response
        table_names = [x.strip() for x in table_list.split(',')]
        print(f"Tables: {table_names}")

    print("Done")
