import os
import pandas as pd

class StoredProcedureToTableMapper:
    """
    This class knows the structure of the DDL statements DataFrame and and iterates through each row
    to find the tables that are manipulated by each procedure.

    It creates a new dataframe that has the following columns:
    table_name, sql_operation, procedure_name

    Code parsing is delegated to the sql_code_parser object.
    """
    CACHE_FILE_NAME = './results/tables_to_procs_cache.csv'

    def __init__(self, sql_code_parser, use_cache=True) -> None:
        self.sql_code_parser = sql_code_parser
        self.use_cache = use_cache


    def _map_sql_operation_to_read_write(self, operation):
        """
        Map the SQL operation to a READ or WRITE operation.
        If the operation is not a DML operation, then return NONE.        
        """
        if operation == 'SELECT':
            return 'READ'
        elif operation in ['INSERT', 'UPDATE', 'DELETE']:
            return 'WRITE'
        else:
            return 'NONE' # In cases where there is neither a READ nor WRITE, such as calling a stored procedure.


    def _execute_mapping(self, ddl_df):
        procedures_ds = ddl_df[ddl_df['sql_operation'] == 'CREATE PROCEDURE']
        procedure_names = procedures_ds['db_object_name'].tolist()

        output_df = pd.DataFrame(columns=['table_name', 'sql_operation', 'operation_type', 'procedure_name'])
        
        for procedure_name in procedure_names:
            
            sql_code = procedures_ds[procedures_ds['db_object_name'] == procedure_name]['sql_code'].values[0]
            procedure_code = self.sql_code_parser.extract_procedure_declaration_from_code(procedure_name, sql_code)
            
            tables = self.sql_code_parser.find_tables_manipulated_by_procedure(procedure_name, procedure_code)
            
            for table in tables:
                new_row = pd.DataFrame([{
                    'table_name': table['table_name'], 
                    'sql_operation': table['sql_operation'], 
                    'operation_type': self._map_sql_operation_to_read_write(table['sql_operation']),
                    'procedure_name': procedure_name
                }])
                output_df = pd.concat([output_df, new_row], ignore_index=True)
        
        return output_df


    def map_procedures_to_tables(self, ddl_df):
        """
        Iterate through each procedure and find the tables that are manipulated by each procedure.
        """
        if self.use_cache and os.path.exists(StoredProcedureToTableMapper.CACHE_FILE_NAME):
            return pd.read_csv(StoredProcedureToTableMapper.CACHE_FILE_NAME)
        else:
            result = self._execute_mapping(ddl_df)
            result.to_csv(StoredProcedureToTableMapper.CACHE_FILE_NAME, index=False)
            return result
    