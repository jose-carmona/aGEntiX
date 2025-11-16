# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aGEntiX** is an AI Agent System designed to integrate with GEX (Gestión de Expedientes), a document and process management system used throughout Córdoba province, Spain. The system enables AI agents to automate tasks within administrative workflows while maintaining strict boundaries on decision-making authority.

## Documentation

The project uses a **Zettelkasten** system for documentation located in the `/doc` directory:
- Each note represents a single concept, requirement, or idea
- Notes are interconnected via `[note-name](note-file.md)` references
- Start with `/doc/index.md` for a complete overview of all topics
- Detailed documentation covers: GEX system, BPMN workflows, agent configuration, architecture principles, and security/permissions

When working on features, consult the relevant notes in `/doc` for detailed context.

### Core Concepts

**GEX System Components:**
- **Document Manager (Gestor Documental)**: Stores and manages documents
- **Process Manager (Gestor de Expedientes)**: Manages case files (expedientes)
- **BPMN Engine**: Orchestrates workflow automation

See `/doc/002-componentes-gex.md` for details.

**Information Flow:**
Citizen → Electronic Portal → GEX → Electronic Notification → Citizen → Feedback

See `/doc/003-flujo-informacion.md` for details.

**Integration Points:**
- Electronic signature system
- Notification system
- Billing/collections (Recaudación)
- Accounting (Contabilidad)

See `/doc/004-integraciones.md` for details.

### Architecture Principles

1. **No Coupling, No Intrusion**: AI agents must not be tightly coupled to GEX
2. **Modularity**: Components should be modular and independently deployable
3. **MCP Access**: Information and tools accessed via Model Context Protocol (MCP)

See `/doc/040-criterios-diseño.md` and `/doc/042-acceso-mcp.md` for architectural details.

### BPMN Workflow Model

**Tasks** decompose into **Actions**:
- Every workflow has a Start Task and End Task (which closes the Expediente)
- Tasks can have multiple next tasks based on conditions
- Tasks can have timeouts that trigger fallback tasks
- Human selection of next task is supported

**New Capability**: Tasks can now include Agent-type actions

See `/doc/020-bpmn-modelo.md` and `/doc/023-acciones-agente.md` for BPMN workflow details.

### AI Agent Design

**Agent Configuration:**
- Name
- System prompt
- URL endpoint
- LLM model
- Task-specific prompt
- Available tools/capabilities

See `/doc/031-configuracion-agente.md` for configuration details.

**Context Provided to Agents:**
- Full Expediente (case file) information
- All documents and data associated with the case

See `/doc/032-contexto-agente.md` for context details.

**Agent Permissions:**
- Read: All information from the Expediente being processed
- Write: Limited by configured permissions
- Authorship: Uses agent name defined in configuration
- Permissions propagate: Agent → MCP → API

See `/doc/050-permisos-agente.md` and `/doc/052-propagacion-permisos.md` for permission system details.

**Audit Requirements:**
- Agents must log all steps for debugging and verification
- Logs ensure actions can be reviewed and validated

See `/doc/033-auditoria-agente.md` for audit requirements.

### Human vs. AI Task Boundaries

**Tasks Reserved for Humans:**
- Legal analysis and decision-making based on regulations
- Final quality control over processes

**Tasks AI Can Automate:**
- Information extraction from incoming documents
- Document generation (beyond basic template substitution)
- Data validation and verification

**Tasks AI Can Assist With:**
- Analysis support for decision-making
- Information summarization
- Pattern detection

**Tasks Already Automated (No AI needed):**
- Numeric operations on external systems (suspend, cancel, create debts)
- Accounting entries
- Basic document generation from templates

See `/doc/010-tipos-tareas.md` through `/doc/013-tareas-ia-candidatas.md` for detailed task categorization.

### Development Strategy

The project follows a **conservative approach**:
- Legal decisions remain exclusively human
- AI augments but does not replace human judgment
- Focus on automating clear-cut tasks first
- Maintain full audit trails for compliance

See `/doc/041-enfoque-conservador.md` for the rationale behind this strategy.

## Language

The primary language of this project is **Spanish**. Code comments, documentation, and domain terminology will be in Spanish as this is a system for Spanish public administration.
