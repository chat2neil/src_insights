from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import pandas as pd
import json

class SqlCodeParser:
    """
    This class contains the functions for parsing SQL code.
    """

    def __init__(self, source_directory, source_file_glob_pattern="**/*.sql", chunk_limit=0, verbose=True):
        """
        Initialise the class with the source directory and the glob pattern for the SQL files to parse.
        """
        self.source_directory = source_directory
        self.source_file_glob_pattern = source_file_glob_pattern
        self.chunk_limit = chunk_limit
        self.verbose = verbose


    def _find_db_objects_in_code(self, sql_code):
        """
        Find all the Data Definition Language (DDL) statements in the SQL CODE fragment
        provided and extract the statement type and the name of the database object 
        being created, altered or dropped.

        Output Format:
        An array, containing the name of the database object and the DDL statement type in UPPERCASE text.
        
        Example:
        [{"db_object_name": "EmployeeID", "dml_operation": "CREATE INDEX"}]
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


    def parse_code(self):
        """
        Reads the SQL code from the files in the source directory and parse the code to 
        extract the Data Definition Language (DDL) statements.

        The output is a dataframe with the following columns:
        - db_object_name: The name of the database object being created, altered or dropped.
        - dml_operation: The type of DDL statement.
        - sql_code: The SQL code that was parsed.

        The dml_operation can be one of the following:
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
            self.source_directory, glob=self.source_file_glob_pattern, loader_cls=TextLoader, show_progress=self.verbose
        )
        documents = loader.load()

        # Split the code into chunks, ideally where there is a GO statement which indicates the end of a significant code block.
        splitter = RecursiveCharacterTextSplitter(
            separators=["GO\n", "go\n", "\n\n", "\n"], chunk_size=2000, chunk_overlap=0, keep_separator=True
        )
        chunks = splitter.split_documents(documents)
        sample_chunks = chunks[0: self.chunk_limit] if self.chunk_limit > 0 else chunks

        ddl_statements_dataframe = pd.DataFrame(columns=['db_object_name', 'dml_operation', 'sql_code'])
        for chunk in sample_chunks:
            content = chunk.page_content
            database_objects = self._find_db_objects_in_code(content)
            temp_df = pd.DataFrame(database_objects)
            temp_df['sql_code'] = content
            ddl_statements_dataframe = pd.concat([ddl_statements_dataframe, temp_df], ignore_index=True)

        return ddl_statements_dataframe


if __name__ == '__main__':
    sql_parser = SqlCodeParser(
        source_directory="source_code/sql_server", 
        source_file_glob_pattern="**/*.sql",
        chunk_limit=3,
        verbose=True)
    df = sql_parser.parse_code()
    df.to_csv('./results/sql_code_parser_results.csv', index=False)
    print(df)
    print("Done!")
