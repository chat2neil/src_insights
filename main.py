from dotenv import load_dotenv
import argparse
from lib.diagram_generator import DiagramGenerator
from lib.service_extractor import ServiceExtractor
from lib.sql_code_parser import SqlCodeParser
from lib.stored_procedure_to_table_mapper import StoredProcedureToTableMapper

load_dotenv()

# Parse the command line arguments
parser = argparse.ArgumentParser(description='Source insigts for SQL code')
parser.add_argument('--debug',
                    action='store_true',
                    help='set to true to run in debug mode, which will only process a small number of files')

parser.add_argument('--no-cache',
                    action='store_true',
                    help='if true, then a cache of previously parsed files will be used; the cache is in CSV format')
args = parser.parse_args()
use_cache = not args.no_cache

print("Running in debug mode") if args.debug else print("Running in production mode")
print("Not using cached results") if args.no_cache else print("Using cached results if they exist")

# Create SQL code parser.
sql_parser = SqlCodeParser(
        source_directory="source_code/sql_server", 
        source_file_glob_pattern="**/*.sql",
        debug=args.debug,
        use_cache=use_cache)

# Parse the SQL code and find the DDL statements
# This returns cached results if the cache exists
# The results are in a Pandas DataFrame with the following columns:
# db_object_name, sql_operation, sql_code
print("\n\nParsing SQL code into a dataframe containing all the DDL statements ...")
ddl_statements_df = sql_parser.find_ddl_statements()

# Output the list of procedures found
procedure_names = ddl_statements_df[ddl_statements_df['sql_operation'] == 'CREATE PROCEDURE']['db_object_name'].tolist()
print("\n\nFound procedures:")
print(procedure_names)

# Output the list of tables found
table_names = ddl_statements_df[ddl_statements_df['sql_operation'] == 'CREATE TABLE']['db_object_name'].tolist()
print("Found tables:")
print(table_names)

# Create a map of procedures to tables
# Note that this step also returns cached results if the cache exists.
# todo: this needs tests
print("\n\nMapping procedures to tables...")
sp_to_table_mapper = StoredProcedureToTableMapper(sql_parser, use_cache=use_cache)
tables_df = sp_to_table_mapper.map_procedures_to_tables(ddl_statements_df)
print("The procedure map looks like the following:")
print(tables_df.head())

# Extract the services from the map of procedures to tables.
# Note that this step also returns cached results if the cache exists.
# todo: this needs tests
service_extractor = ServiceExtractor(tables_df, use_cache=use_cache)
service_definitions = service_extractor.extract()
print("\n\nFound services:")
for service_definition in service_definitions:
    print(service_definition)

# Generate diagrams for each service definition.
# todo: this needs tests
print("\n\nGenerating diagrams...")
diagram_generator = DiagramGenerator()
diagram_generator.generate(service_definitions)

print("Done.")
