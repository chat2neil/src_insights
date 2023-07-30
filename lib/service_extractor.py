import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

from lib.service_definition import ServiceDefinition

class ServiceExtractor:
    """
    Extracts services from a data frame that contains a list of tables mapped to stored procedures by operation type.
    
    The extractor aims to group stored procedures together, based on their names, the table names and the table 
    operations.  The grouping favors stored procedures that write to tables, over stored procedures that only read from tables.

    The extractor expects a data frame with the following columns:
    - procedure_name: The name of the stored procedure
    - table_name: The name of the table that the stored procedure reads from or writes to
    - operation_type: The type of operation that the stored procedure performs on the table (read or write)
    """

    CACHE_FILE_NAME = './results/service_candidates_cache.csv'

    def __init__(self, tables_df, number_of_clusters=5, use_cache=False) -> None:
        self.tables_df = tables_df
        self.number_of_clusters = number_of_clusters
        self.use_cache = use_cache


    def _cluster_procedures_by_table_and_operation(self, df):
        """
        Cluster the procedures by the tables that they operate on and the operation type.

        Adds the following columns to the data frame:
        - cluster_label: The cluster label that the procedure belongs to
        - combined_feature: The combined feature that was used to cluster the procedure
        """
        # Step 1: Define the features that you want to use to cluster the records
        # Combine 'table_name' and 'procedure_name' into a single feature
        df['combined_feature'] = df['table_name'] + ' ' + df['procedure_name'] + ' ' + df['operation_type']

        # Convert the 'combined_feature' column to a matrix of TF-IDF features
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(df['combined_feature'])

        # Step 2: Use a clustering algorithm to cluster the records based on these features
        # Let's use KMeans as an example
        kmeans = KMeans(n_clusters=self.number_of_clusters)
        kmeans.fit(X)

        # Assign the cluster labels to the records
        df['cluster_label'] = kmeans.labels_
        return df
    

    def _replace_spaces_with_underscores_in_names(self, df):
        """
        Replace spaces with underscores in the service_name, table_name and procedure_name columns
        """
        for col in ['procedure_name', 'table_name']:
            df[col] = df[col].str.replace(' ', '_')
        return df


    def _derive_service_name(self, group):
        """
        Derive the service name for a group of rows, containing the table_name and operation_type columns.

        Base service names on the most common table that it writes to, if possible.
        """
        group_write = group[group['operation_type'] == 'WRITE']

        if group_write.empty:
            if group.size > 0:
                most_common_table = group['table_name'].value_counts().idxmax()
                return most_common_table
            else:
                return 'Service With No Name'

        most_common_table = group_write['table_name'].value_counts().idxmax()
        return most_common_table


    def _add_derived_service_name_for_each_cluster_based_on_most_common_table_name(self, df):
        # Derive the service name for each cluster, pass the table_name and operation_type columns 
        # to the derive_service_name function.  Assign the service names to a new column called service_name.
        service_names = df.groupby('cluster_label')[['table_name', 'operation_type']].apply(self._derive_service_name).reset_index()
        service_names.columns = ['cluster_label', 'service_name']

        # Merge the service names into the original DataFrame
        df = pd.merge(df, service_names, on='cluster_label')

        return df
      

    def _convert_dataframe_to_service_definitions(self, df):
        """
        Converts the dataframe to a list of ServiceDefinition objects.
        """
        result = []
        for cluster_label in df['cluster_label'].unique():
            cluster_df = df[df['cluster_label'] == cluster_label]
            
            service_name = cluster_df['service_name'].iloc[0]
            procs = cluster_df['procedure_name'].tolist()
            read_tables = cluster_df[cluster_df['operation_type'] == 'READ']['table_name'].tolist()
            write_tables = cluster_df[cluster_df['operation_type'] == 'WRITE']['table_name'].tolist()
            result.append(ServiceDefinition(service_name, procs, read_tables, write_tables))
        
        return result


    def extract(self):
        """
        Perform the service extraction process.
        """
        # If the cache file exists, then read the results from the cache file and don't alter it.
        # This allows for manual tweaking of the cached information.
        if self.use_cache and os.path.exists(self.CACHE_FILE_NAME):
            df = pd.read_csv(self.CACHE_FILE_NAME)
        else:
            df = self._replace_spaces_with_underscores_in_names(self.tables_df)
            df = self._cluster_procedures_by_table_and_operation(df)
            df = self._add_derived_service_name_for_each_cluster_based_on_most_common_table_name(df)
            df.to_csv(self.CACHE_FILE_NAME, index=False)

        return self._convert_dataframe_to_service_definitions(df)

