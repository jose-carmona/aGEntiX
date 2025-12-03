# Memoria Inicial del Proyecto Capstone aGEntiX

## Introducción

GEX (Gestión de Expedientes) es la aplicación central de gestión administrativa desarrollada por Eprinsa, la Empresa Provincial de Informática de la Excma. Diputación Provincial de Córdoba, España. Este sistema constituye el núcleo vertebrador de la administración electrónica tanto en el sector público institucional de la Diputación como en la práctica totalidad de los Ayuntamientos de la provincia cordobesa a los que la Diputación presta servicios tecnológicos.

En el contexto actual de la administración pública, la incorporación de inteligencia artificial representa una oportunidad para optimizar procesos administrativos que, si bien no requieren toma de decisiones complejas, superan las capacidades de los sistemas de automatización tradicionales. La presente propuesta plantea la integración de agentes de IA en GEX mediante una arquitectura desacoplada, modular y segura, que permita automatizar tareas operativas manteniendo en todo momento la supervisión humana en decisiones que impliquen responsabilidad legal o análisis normativo.  

## Título y Concepto Central

**aGEntiX - Sistema de Agentes IA para Automatización de Workflows en GEX**

### Concepto Central

aGEntiX es un sistema que permite la integración de agentes de inteligencia artificial con GEX. El concepto central es **incorporar capacidades de IA en flujos de trabajo BPMN existentes**, permitiendo que agentes IA automaticen tareas específicas dentro de expedientes administrativos, manteniendo al mismo tiempo estrictos límites en la autoridad de toma de decisiones y garantizando la supervisión humana donde sea necesaria.

La propuesta introduce un nuevo tipo de acción en el modelo BPMN de GEX: las **acciones de tipo Agente**, que permiten delegar tareas específicas a agentes IA configurables, sin acoplar el sistema de IA al núcleo de GEX.

## Objetivos

### 1. Automatizar tareas administrativas de bajo riesgo que actualmente requieren intervención humana

**Problema que resuelve**: Muchas tareas administrativas son repetitivas, consumen tiempo valioso del personal y no requieren toma de decisiones complejas, pero superan las capacidades de los sistemas de automatización tradicionales basados en plantillas.

**Qué se propone conseguir**:
- Automatizar la **extracción de información** de documentos entrantes (solicitudes, certificados, formularios) para poblar expedientes automáticamente
- Implementar **generación avanzada de documentos** que vaya más allá de la simple sustitución de plantillas, produciendo documentos contextualizados basados en la información del expediente
- Reducir la carga de trabajo manual del personal administrativo en tareas operativas

### 2. Asistir en el análisis de información sin reemplazar el juicio humano

**Problema que resuelve**: Los funcionarios deben revisar grandes cantidades de información y documentación para tomar decisiones administrativas. La capacidad de análisis y síntesis de IA puede acelerar este proceso, pero las decisiones legales deben permanecer en manos humanas por su responsabilidad legal.

**Qué se propone conseguir**:
- Proporcionar **análisis y resúmenes** de información relevante para ayudar en la toma de decisiones
- Identificar **patrones, inconsistencias o elementos relevantes** en la documentación
- Mantener el control y responsabilidad final en manos del funcionario humano, con IA en rol de asistencia

### 3. Garantizar la integración segura y desacoplada de IA en sistemas críticos de administración pública

**Problema que resuelve**: Integrar IA en sistemas de administración pública presenta desafíos únicos: requisitos de auditoría, protección de datos, responsabilidad legal, y la necesidad de evolución independiente de componentes.

**Qué se propone conseguir**:
- Arquitectura **desacoplada** donde los agentes IA no están integrados directamente en GEX, permitiendo actualizaciones independientes
- Sistema de **permisos granular** que limite el acceso de los agentes al expediente específico en proceso
- **Trazabilidad completa** de todas las acciones realizadas por agentes mediante logging exhaustivo
- Acceso a información y herramientas mediante **Model Context Protocol (MCP)**, estableciendo una capa de abstracción estándar

### 4. Adoptar un enfoque conservador que prioriza la seguridad jurídica

**Problema que resuelve**: La incorporación precipitada de IA en procesos administrativos podría generar decisiones incorrectas, problemas legales o pérdida de confianza ciudadana.

**Qué se propone conseguir**:
- Establecer límites claros: **las decisiones legales y análisis normativos permanecen exclusivamente humanos**
- Comenzar con casos de uso de **bajo riesgo** (extracción de información, generación de documentos)
- Permitir **evolución gradual** del sistema, ampliando capacidades según se gane experiencia y confianza
- Diseñar flujos BPMN con **puntos de supervisión humana** obligatorios en decisiones críticas

### 5. Crear un sistema modular, escalable y reutilizable

**Problema que resuelve**: Las soluciones monolíticas son difíciles de mantener, actualizar y extender. Se requiere flexibilidad para adaptarse a diferentes tipos de procedimientos administrativos.

**Qué se propone conseguir**:
- Arquitectura **modular** con componentes independientemente desplegables
- Agentes **configurables** mediante parámetros (prompt de sistema, modelo LLM, herramientas disponibles, permisos)
- Posibilidad de crear diferentes agentes especializados para distintos tipos de tareas
- Sistema **reutilizable** en diferentes tipos de expedientes y procedimientos

## Viabilidad

El proyecto se considera viable por las siguientes razones:

1. **Base tecnológica sólida**: Utiliza tecnologías maduras (Python, FastAPI, Model Context Protocol) y modelos LLM disponibles comercialmente

2. **Integración no invasiva**: El diseño desacoplado permite incorporar IA sin modificar el núcleo de GEX, reduciendo riesgos técnicos

3. **Alcance acotado inicialmente**: El enfoque conservador limita el alcance inicial a tareas de bajo riesgo, permitiendo validación progresiva

4. **Sistema de permisos existente**: GEX ya dispone de un sistema de permisos y un usuario "Automático" para acciones del sistema, que puede aprovecharse para los agentes IA

5. **Infraestructura BPMN existente**: El modelo de workflows BPMN de GEX proporciona el marco estructural donde integrar las acciones de agente

## Claridad de la Propuesta

La propuesta es clara en:

- **Qué automatizar**: Extracción de información y generación de documentos
- **Qué no automatizar**: Decisiones legales y análisis normativos
- **Cómo integrarlo**: Mediante acciones de tipo Agente en flujos BPMN, accediendo a GEX vía MCP
- **Qué proteger**: Datos mediante sistema de permisos, decisiones mediante supervisión humana, trazabilidad mediante auditoría completa
