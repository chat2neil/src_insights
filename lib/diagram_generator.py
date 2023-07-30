
import subprocess
from typing import List
from jinja2 import Template
from lib.service_definition import ServiceDefinition

class DiagramGenerator:
    """
    Genaerates multiple diagrams based on the serive definitions provided.
    """

    DIAGRAM_TEMPLATE = """
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

    def __init__(self) -> None:
        self.template = Template(DiagramGenerator.DIAGRAM_TEMPLATE)
    

    def _generate_diagram(self, service_definition: ServiceDefinition) -> None:
        """
        Generate a diagram for a single service definition.
        """
        rendered_text = self.template.render(
             service_name= service_definition.service_name, 
             procedures=service_definition.procs, 
             read_tables=service_definition.read_tables, 
             write_tables=service_definition.write_tables)
        # print(rendered_text)

        diagram_path = f"./results/{service_definition.service_name}.puml"
        with open(diagram_path, 'w') as file:
                file.write(rendered_text)

        cmd = f'plantuml {diagram_path}'
        subprocess.run(cmd, shell=True, check=True)



    def generate(self, service_definitions: List[ServiceDefinition]) -> None:
        """
        Generate diagrams for each service definition.
        """
        for service_definition in service_definitions:
            self._generate_diagram(service_definition)
