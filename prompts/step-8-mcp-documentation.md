Se desea crear un nuevo conjunto de herramientas MCP disponibles para los agentes: se trata de la documentación asociada al **tipo de Expediente**.

Documentación asociada al tipo de Expedientes:
* Normativa regulatoria.
* Indicaciones sobre la instrucción de los expedientes del tipo concreto:
  * Documentación necesaria para la tramitación.
  * Plazos.
  * Criterios para la aprobación o denegación.
  * Etc.
* Documentos plantilla (por ejemplo, Documento platilla de propuesta de resolución, Documento de requerimiento de documentación faltante, etc.).
* Etc.

Dicha información es esencial para la tramitación del expediente.

El agente tendrá acceso a dicha información mediante MCP accediendo por el tipo de Expediente.

Estructura de directorios:

/src/mcp_mock/data/documentos/<tipo_de_expediente>/<tipo_documento>.json

Cada documento tendrá:
* Descripción del documento, que indicará el objetivo del documento y su uso.
* Intrucciones de uso para el agente.
* Contenido del documento en markdown.

Tendremos 3 tipos de Expedientes:
* subvenciones
* licencias de obras
* certificado de empadronamiento
