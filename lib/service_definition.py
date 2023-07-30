
class ServiceDefinition:

    def __init__(self, service_name, procs = [], read_tables = [], write_tables = []) -> None:
        self.service_name = service_name
        self.procs = procs
        self.read_tables = read_tables
        self.write_tables = write_tables

    def __str__(self) -> str:
        return f"ServiceDefinition: {self.service_name} (procs: {self.procs}, read_tables: {self.read_tables}, write_tables: {self.write_tables})"
