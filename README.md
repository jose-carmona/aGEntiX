# aGEntiX

**Sistema de Agentes IA para Automatización de Workflows Administrativos en GEX**

## Descripción

**aGEntiX** es un sistema que permite la integración de agentes de inteligencia artificial con GEX (Gestión de Expedientes) para automatizar tareas específicas dentro de los flujos de trabajo administrativos, manteniendo límites estrictos en la autoridad de toma de decisiones y garantizando la supervisión humana donde sea necesaria.

GEX es la aplicación central de gestión administrativa desarrollada por Eprinsa (Empresa Provincial de Informática de la Excma. Diputación Provincial de Córdoba, España), y constituye el núcleo vertebrador de la administración electrónica en la provincia de Córdoba, utilizado tanto por el sector público institucional de la Diputación como por la práctica totalidad de los Ayuntamientos de la provincia.

## Concepto Central

La propuesta de aGEntiX introduce un nuevo tipo de acción en el modelo BPMN de GEX: las **acciones de tipo Agente**. Este enfoque permite:

- **Automatizar tareas operativas**: Extracción de información de documentos entrantes y generación avanzada de documentos contextualizados
- **Asistir en análisis de información**: Proporcionar resúmenes, identificar patrones y elementos relevantes para ayudar en la toma de decisiones
- **Mantener supervisión humana**: Las decisiones legales y análisis normativos permanecen exclusivamente en manos de funcionarios humanos
- **Arquitectura desacoplada**: Los agentes IA no están acoplados directamente a GEX, permitiendo evolución independiente de componentes

## Objetivos del Proyecto

### 1. Automatizar tareas administrativas de bajo riesgo

Reducir la carga de trabajo manual del personal administrativo en tareas repetitivas que no requieren decisiones complejas, pero superan las capacidades de los sistemas de automatización tradicionales basados en plantillas.

### 2. Asistir en el análisis de información sin reemplazar el juicio humano

Proporcionar herramientas de análisis y síntesis de información que aceleren la revisión de documentación, manteniendo el control y responsabilidad final en manos del funcionario humano.

### 3. Garantizar integración segura y desacoplada

Implementar una arquitectura con permisos granulares, trazabilidad completa y acceso a través de Model Context Protocol (MCP), que permita actualizaciones independientes sin modificar el núcleo de GEX.

### 4. Adoptar un enfoque conservador

Comenzar con casos de uso de bajo riesgo, establecer límites claros en la toma de decisiones, y permitir evolución gradual del sistema según se gane experiencia y confianza.

### 5. Crear un sistema modular, escalable y reutilizable

Desarrollar agentes configurables que puedan adaptarse a diferentes tipos de procedimientos administrativos mediante parámetros como prompts de sistema, modelos LLM, herramientas disponibles y permisos específicos.

## Principios de Diseño

1. **No acoplamiento**: Los agentes IA no están acoplados a GEX, permitiendo evolución independiente
2. **Modularidad**: Componentes independientemente desplegables y actualizables
3. **Acceso vía MCP**: Información y herramientas accesibles mediante Model Context Protocol (estándar de la industria)
4. **Enfoque conservador**: Las decisiones legales permanecen exclusivamente humanas con supervisión obligatoria
5. **Auditoría completa**: Todos los pasos del agente quedan registrados para debugging, verificación y cumplimiento normativo

## Viabilidad del Proyecto

El proyecto se considera viable por las siguientes razones:

- **Base tecnológica sólida**: Utiliza tecnologías maduras (Python, FastAPI, Model Context Protocol) y modelos LLM disponibles comercialmente
- **Integración no invasiva**: El diseño desacoplado permite incorporar IA sin modificar el núcleo de GEX, reduciendo riesgos técnicos
- **Alcance acotado inicialmente**: El enfoque conservador limita el alcance inicial a tareas de bajo riesgo, permitiendo validación progresiva
- **Sistema de permisos existente**: GEX ya dispone de un sistema de permisos y un usuario "Automático" para acciones del sistema, que puede aprovecharse para los agentes IA
- **Infraestructura BPMN existente**: El modelo de workflows BPMN de GEX proporciona el marco estructural donde integrar las acciones de agente

## Documentación

### Memoria del Proyecto

Para una visión completa y detallada del proyecto, consulta la [Memoria Inicial del Proyecto Capstone](doc/memoria.md) ([versión PDF](doc/memoria.pdf)), que incluye:

- Introducción contextualizada sobre GEX y la oportunidad de integración de IA
- Descripción detallada de los 5 objetivos principales del proyecto
- Análisis de viabilidad técnica y organizativa
- Clarificación del alcance: qué se automatiza y qué permanece exclusivamente humano

### Sistema de Notas Zettelkasten

La documentación técnica completa del proyecto está organizada en un sistema **Zettelkasten** en el directorio `/doc`, donde cada nota representa un concepto individual e incluye referencias a notas relacionadas.

**Punto de entrada**: [doc/index.md](doc/index.md)

**Temas principales cubiertos:**

- **Sistema GEX**: Componentes, flujos de información e integraciones → [doc/001-gex-definicion.md](doc/001-gex-definicion.md)
- **Automatización de Tareas**: Tipos de tareas y candidatas para IA → [doc/010-tipos-tareas.md](doc/010-tipos-tareas.md)
- **Modelo BPMN**: Estructura de workflows y acciones de agente → [doc/020-bpmn-modelo.md](doc/020-bpmn-modelo.md)
- **Agentes IA**: Configuración, contexto y auditoría → [doc/030-propuesta-agentes.md](doc/030-propuesta-agentes.md)
- **Arquitectura**: Criterios de diseño y acceso MCP → [doc/040-criterios-diseño.md](doc/040-criterios-diseño.md)
- **Permisos**: Sistema de permisos y propagación → [doc/050-permisos-agente.md](doc/050-permisos-agente.md)
- **Análisis Crítico**: Problemas identificados y prioridades de mejora → [doc/problemas/100-problematica-general.md](doc/problemas/100-problematica-general.md)

## Getting Started

### Opción Recomendada: Dev Container

El proyecto está configurado para usar **Dev Containers** de VS Code, que proporciona un entorno de desarrollo completamente configurado:

**Requisitos:**

- Docker Desktop instalado y ejecutándose
- Visual Studio Code con la extensión Dev Containers

**Inicio rápido:**

1. Abre el proyecto en VS Code
2. Haz clic en "Reopen in Container" cuando aparezca la notificación
3. Espera a que el container se construya (primera vez: ~5-10 min)
4. ¡Listo! El entorno incluye Python, Node.js, herramientas MCP y todas las dependencias

Ver [.devcontainer/README.md](.devcontainer/README.md) para documentación completa.

### Opción Alternativa: Instalación Local

Si prefieres trabajar sin Dev Containers:

```bash
# Instalar dependencias Python
cd mcp-mock/mcp-expedientes
pip install -r requirements.txt

# Instalar herramientas MCP (opcional)
npm install -g @modelcontextprotocol/inspector

# Ejecutar tests
pytest
```

## Ejecución de Tests

El proyecto incluye un script para ejecutar los tests desde la raíz del proyecto:

```bash
# Ejecutar todos los tests
./run-tests.sh

# Ejecutar con output verbose
./run-tests.sh -v

# Ejecutar solo tests de autenticación
./run-tests.sh -k auth

# Ejecutar solo tests de tools
./run-tests.sh -k tools

# Detener en el primer error
./run-tests.sh -x

# Re-ejecutar solo tests fallidos
./run-tests.sh --failed

# Ver todas las opciones disponibles
./run-tests.sh --help
```

### Alternativa: Ejecución manual desde el directorio de tests

```bash
cd mcp-mock/mcp-expedientes

# Test rápido
./quick_test.sh

# Ejecutar tests completos
pytest -v
```

**Nota:** Los tests utilizan archivos `.backup` para mantener datos limpios entre ejecuciones. Los archivos originales se restauran automáticamente antes de cada test que modifica datos.

## Quick Start - Servidor MCP Mock

```bash
# Dentro del Dev Container o con dependencias instaladas
cd mcp-mock/mcp-expedientes

# Iniciar servidor HTTP
python -m uvicorn server_http:app --reload --port 8000
```
