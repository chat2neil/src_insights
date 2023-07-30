from dotenv import load_dotenv
import argparse
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from jinja2 import Template
import subprocess
from lib.sql_code_parser import SqlCodeParser

load_dotenv()


def list_procedure_names(df):
    """
    Find all the procedure names in the source insights data frame.
    """
    procedures = df[df['sql_operation'] == 'CREATE PROCEDURE']
    return procedures['db_object_name'].to_list()


def list_table_names(df):
    """
    Find all the table names in the source insights data frame.
    """
    tables = df[df['sql_operation'] == 'CREATE TABLE']
    return tables['db_object_name'].to_list()



def group_tables_by_dml_operation(array_of_table_names_and_dml_operations):
    """
    Given an array of dictionaries, group the dictionaries by the sql_operation key
    and return a dictionary with the sql_operation as the key and the table_name as the value.

    Example:
    Input: [{'table_name': 'Orders', 'sql_operation': 'SELECT'}, {'table_name': 'Order Subtotals', 'sql_operation': 'SELECT'}]
    Output: {'SELECT': 'Orders, Order Subtotals'}
    """
    dict_by_operation = {}

    # Iterate over the array
    for item in array_of_table_names_and_dml_operations:
        # If the sql_operation is not in the dictionary, add it with the table_name as the value
        if item['sql_operation'] not in dict_by_operation:
            dict_by_operation[item['sql_operation']] = item['table_name']
        # If the sql_operation is already in the dictionary, append the table_name to the existing value
        else:
            dict_by_operation[item['sql_operation']] += ', ' + item['table_name']
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
parser.add_argument('--debug',
                    action='store_true',
                    help='set to true to run in debug mode, which will only process a small number of files')

parser.add_argument('--no-cache',
                    action='store_true',
                    help='if true, then a cache of previously parsed files will be used; the cache is in CSV format')
args = parser.parse_args()

print("Running in debug mode") if args.debug else print("Running in production mode")
print("Not using cached results") if args.no_cache else print("Using cached results if they exist")

sql_parser = SqlCodeParser(
        source_directory="source_code/sql_server", 
        source_file_glob_pattern="**/*.sql",
        debug=args.debug,
        use_cache=(not args.no_cache))

# Parse the SQL code and find the DDL statements
# This returns cached results if the cache exists
# The results are in a Pandas DataFrame with the following columns:
# db_object_name, sql_operation, sql_code
df = sql_parser.find_ddl_statements()

procedure_names = list_procedure_names(df)
print("\n\nFound procedures:")
print(procedure_names)

table_names = list_table_names(df)
print("Found tables:")
print(table_names)

print("Done.")
