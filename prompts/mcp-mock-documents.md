# Ampliación del MCP Mock: Funcionalidad de Documentos

## Contexto

Ver documento `/prompts/make-mcp-mock.md`

Siguiendo ese documento se implementó un servidor mock MCP sobre expedientes. Ver fuentes bajo `/src/mcp_mock/mcp_expedientes/`

Se desea ampliar la funcionalidad del mock en relación con el objeto "Documento" para soportar extracción de texto y metadatos.

## Modelo de Datos: Documento

### Estructura Actual (ya existe)

```python
class Documento(BaseModel):
    id: str                      # ID único (ej: "DOC-001")
    nombre: str                  # Nombre del fichero (ej: "dni.pdf")
    fecha: datetime              # Fecha de incorporación al expediente
    tipo: str                    # Tipo de documento (SOLICITUD, IDENTIFICACION, BANCARIO, etc.)
    ruta: str                    # Ruta física del documento
    hash_sha256: str             # Hash para verificar integridad
    tamano_bytes: int            # Tamaño en bytes
    validado: Optional[bool]     # Estado de validación
```

### Nuevos Campos a Añadir

```python
class Documento(BaseModel):
    # ... campos existentes ...

    # NUEVOS CAMPOS
    metadatos_extraidos: Optional[Dict[str, Any]] = None
    """
    Metadatos extraídos del documento según su tipo.

    Ejemplos por tipo de documento:

    IDENTIFICACION (DNI/NIE):
    {
        "numero_documento": "12345678A",
        "tipo_documento": "DNI",
        "nombre_completo": "María García López",
        "fecha_nacimiento": "1985-03-15",
        "fecha_expedicion": "2020-01-10",
        "fecha_caducidad": "2030-01-10",
        "sexo": "F",
        "nacionalidad": "ESPAÑOLA"
    }

    ESCRITURAS (compra/venta, propiedad):
    {
        "referencia_catastral": "1234567VK4712A0001WX",
        "direccion_inmueble": "Calle Mayor 123, Córdoba",
        "tipo_inmueble": "VIVIENDA",
        "superficie_m2": 85.5,
        "notario": "Juan Pérez González",
        "numero_protocolo": "1234/2024",
        "fecha_escritura": "2024-01-10"
    }

    PODER_NOTARIAL:
    {
        "poderdante": "María García López",
        "apoderado": "Antonio Martínez Ruiz",
        "tipo_poder": "GENERAL",
        "notario": "Juan Pérez González",
        "numero_protocolo": "5678/2024",
        "fecha_otorgamiento": "2024-01-05",
        "alcance": ["gestión administrativa", "representación ante organismos públicos"]
    }

    BANCARIO (certificado/justificante):
    {
        "entidad": "Banco Ejemplo",
        "numero_cuenta": "ES79 2100 0813 4501 2345 6789",
        "tipo_cuenta": "CORRIENTE",
        "titular": "María García López",
        "fecha_certificado": "2024-01-14"
    }

    SOLICITUD:
    {
        "tipo_procedimiento": "SUBVENCIONES",
        "fecha_solicitud": "2024-01-15",
        "solicitante": "María García López",
        "nif_solicitante": "12345678A",
        "importe_solicitado": 5000.00,
        "concepto": "Ayuda para mejora de local comercial"
    }

    INFORME:
    {
        "tipo_informe": "TÉCNICO",
        "autor": "Agente ValidadorDocumental",
        "fecha_emision": "2024-01-16",
        "resultado": "FAVORABLE",
        "observaciones": ["Documentación completa", "NIF verificado"]
    }
    """

    texto_markdown: Optional[str] = None
    """
    Texto en markdown que representa fielmente el contenido del documento.

    Este campo contiene una transcripción legible del documento en formato markdown,
    útil para que los agentes IA puedan leer y analizar el contenido sin necesidad
    de procesar el fichero original (PDF, imagen, etc.).

    Ejemplo para un DNI:

    ```markdown
    # Documento Nacional de Identidad

    **ESPAÑA**

    | Campo | Valor |
    |-------|-------|
    | Apellidos | GARCÍA LÓPEZ |
    | Nombre | MARÍA |
    | Sexo | F |
    | Nacionalidad | ESPAÑOLA |
    | Fecha de nacimiento | 15 03 1985 |
    | Número | 12345678A |
    | Fecha de expedición | 10 01 2020 |
    | Válido hasta | 10 01 2030 |

    [Fotografía del titular]
    [Firma del titular]
    ```
    """
```

## Tipos de Documento Soportados

| Tipo | Descripción | Metadatos Clave |
|------|-------------|-----------------|
| `SOLICITUD` | Formulario de solicitud | solicitante, nif, importe, concepto |
| `IDENTIFICACION` | DNI, NIE, Pasaporte | numero_documento, nombre, fechas |
| `BANCARIO` | Certificado/justificante bancario | entidad, cuenta, titular |
| `ESCRITURAS` | Escrituras de propiedad | referencia_catastral, direccion, notario |
| `PODER_NOTARIAL` | Poderes notariales | poderdante, apoderado, alcance |
| `INFORME` | Informes técnicos/administrativos | tipo, autor, resultado |
| `RESOLUCION` | Resoluciones administrativas | tipo, fecha, sentido |
| `NOTIFICACION` | Notificaciones al interesado | destinatario, fecha, asunto |
| `CERTIFICADO` | Certificados oficiales | emisor, fecha, contenido |
| `OTRO` | Documentos no clasificados | descripcion |

## Nuevas Tools MCP

### Tools de Lectura

#### 1. `obtener_texto_documento`

Obtiene el texto markdown del documento para su análisis por el agente.

```python
types.Tool(
    name="obtener_texto_documento",
    description="Obtiene el texto markdown del contenido de un documento",
    inputSchema={
        "type": "object",
        "properties": {
            "expediente_id": {
                "type": "string",
                "description": "ID del expediente (ej: EXP-2024-001)"
            },
            "documento_id": {
                "type": "string",
                "description": "ID del documento (ej: DOC-001)"
            }
        },
        "required": ["expediente_id", "documento_id"]
    }
)
```

**Respuesta:**

```json
{
    "success": true,
    "documento_id": "DOC-002",
    "nombre": "dni.pdf",
    "tipo": "IDENTIFICACION",
    "texto_markdown": "# Documento Nacional de Identidad\n\n**ESPAÑA**\n\n| Campo | Valor |\n|-------|-------|\n| Apellidos | GARCÍA LÓPEZ |\n..."
}
```

**Errores:**
- `404`: Documento no encontrado
- `422`: El documento no tiene texto markdown disponible

#### 2. `obtener_metadatos_documento`

Obtiene los metadatos extraídos del documento.

```python
types.Tool(
    name="obtener_metadatos_documento",
    description="Obtiene los metadatos extraídos de un documento (NIF, fechas, importes, etc.)",
    inputSchema={
        "type": "object",
        "properties": {
            "expediente_id": {
                "type": "string",
                "description": "ID del expediente"
            },
            "documento_id": {
                "type": "string",
                "description": "ID del documento"
            }
        },
        "required": ["expediente_id", "documento_id"]
    }
)
```

**Respuesta:**

```json
{
    "success": true,
    "documento_id": "DOC-002",
    "nombre": "dni.pdf",
    "tipo": "IDENTIFICACION",
    "metadatos_extraidos": {
        "numero_documento": "12345678A",
        "tipo_documento": "DNI",
        "nombre_completo": "María García López",
        "fecha_nacimiento": "1985-03-15",
        "fecha_caducidad": "2030-01-10"
    }
}
```

**Errores:**
- `404`: Documento no encontrado
- `422`: El documento no tiene metadatos extraídos

### Tools de Escritura

#### 3. `actualizar_metadatos_documento`

Actualiza los metadatos extraídos de un documento existente.

```python
types.Tool(
    name="actualizar_metadatos_documento",
    description="Actualiza los metadatos extraídos de un documento",
    inputSchema={
        "type": "object",
        "properties": {
            "expediente_id": {
                "type": "string",
                "description": "ID del expediente"
            },
            "documento_id": {
                "type": "string",
                "description": "ID del documento"
            },
            "metadatos": {
                "type": "object",
                "description": "Metadatos a establecer o actualizar (se mezclan con los existentes)"
            },
            "reemplazar": {
                "type": "boolean",
                "description": "Si true, reemplaza todos los metadatos. Si false, los mezcla (default: false)"
            }
        },
        "required": ["expediente_id", "documento_id", "metadatos"]
    }
)
```

**Ejemplo de uso:**

```json
{
    "expediente_id": "EXP-2024-001",
    "documento_id": "DOC-002",
    "metadatos": {
        "validado_por_agente": true,
        "fecha_validacion": "2024-01-16T10:30:00Z",
        "nif_verificado": true
    },
    "reemplazar": false
}
```

**Respuesta:**

```json
{
    "success": true,
    "documento_id": "DOC-002",
    "metadatos_anteriores": {
        "numero_documento": "12345678A",
        "nombre_completo": "María García López"
    },
    "metadatos_nuevos": {
        "numero_documento": "12345678A",
        "nombre_completo": "María García López",
        "validado_por_agente": true,
        "fecha_validacion": "2024-01-16T10:30:00Z",
        "nif_verificado": true
    },
    "mensaje": "Metadatos actualizados correctamente"
}
```

**Permisos:** Requiere permiso `gestion`

#### 4. `crear_documento_desde_markdown`

Crea un nuevo documento a partir de texto markdown (generado por el agente).

```python
types.Tool(
    name="crear_documento_desde_markdown",
    description="Crea un nuevo documento a partir de contenido markdown generado por el agente",
    inputSchema={
        "type": "object",
        "properties": {
            "expediente_id": {
                "type": "string",
                "description": "ID del expediente"
            },
            "nombre": {
                "type": "string",
                "description": "Nombre del documento (ej: informe_validacion.md)"
            },
            "tipo": {
                "type": "string",
                "description": "Tipo de documento (INFORME, RESOLUCION, NOTIFICACION, etc.)"
            },
            "texto_markdown": {
                "type": "string",
                "description": "Contenido del documento en formato markdown"
            },
            "metadatos": {
                "type": "object",
                "description": "Metadatos del documento (opcional)"
            }
        },
        "required": ["expediente_id", "nombre", "tipo", "texto_markdown"]
    }
)
```

**Ejemplo de uso:**

```json
{
    "expediente_id": "EXP-2024-001",
    "nombre": "informe_validacion_documentos.md",
    "tipo": "INFORME",
    "texto_markdown": "# Informe de Validación de Documentos\n\n## Expediente: EXP-2024-001\n\n### Resultado: FAVORABLE\n\n...",
    "metadatos": {
        "tipo_informe": "VALIDACION_DOCUMENTAL",
        "autor": "Agente ValidadorDocumental",
        "fecha_emision": "2024-01-16T10:45:00Z",
        "resultado": "FAVORABLE",
        "documentos_revisados": ["DOC-001", "DOC-002", "DOC-003"]
    }
}
```

**Respuesta:**

```json
{
    "success": true,
    "documento_id": "DOC-004",
    "nombre": "informe_validacion_documentos.md",
    "tipo": "INFORME",
    "ruta": "data/documentos/EXP-2024-001/informe_validacion_documentos.md",
    "mensaje": "Documento DOC-004 creado correctamente"
}
```

**Permisos:** Requiere permiso `gestion`

## Actualización de Datos Mock

### Estructura de Directorio de Documentos

```
src/mcp_mock/mcp_expedientes/data/
├── expedientes/
│   ├── EXP-2024-001.json
│   ├── EXP-2024-002.json
│   └── EXP-2024-003.json
└── documentos/                    # NUEVO: Contenido markdown de documentos
    ├── EXP-2024-001/
    │   ├── DOC-001-solicitud.md
    │   ├── DOC-002-dni.md
    │   └── DOC-003-justificante_bancario.md
    ├── EXP-2024-002/
    │   └── ...
    └── EXP-2024-003/
        └── ...
```

### Actualizar EXP-2024-001.json

Los documentos deben incluir los nuevos campos:

```json
{
  "documentos": [
    {
      "id": "DOC-001",
      "nombre": "solicitud.pdf",
      "fecha": "2024-01-15T08:30:00Z",
      "tipo": "SOLICITUD",
      "ruta": "data/documentos/EXP-2024-001/solicitud.pdf",
      "hash_sha256": "abc123...",
      "tamano_bytes": 245678,
      "validado": null,
      "metadatos_extraidos": {
        "tipo_procedimiento": "SUBVENCIONES",
        "fecha_solicitud": "2024-01-15",
        "solicitante": "María García López",
        "nif_solicitante": "12345678A",
        "importe_solicitado": 5000.00,
        "concepto": "Ayuda para mejora de local comercial",
        "datos_contacto": {
          "email": "maria.garcia@example.com",
          "telefono": "+34 600123456"
        }
      },
      "texto_markdown": "# Solicitud de Subvención\n\n## Datos del Solicitante\n\n| Campo | Valor |\n|-------|-------|\n| Nombre | María García López |\n| NIF | 12345678A |\n| Dirección | Calle Mayor 123, Córdoba |\n| Email | maria.garcia@example.com |\n| Teléfono | +34 600123456 |\n\n## Datos de la Solicitud\n\n**Concepto:** Ayuda para mejora de local comercial\n\n**Importe solicitado:** 5.000,00 EUR\n\n**Cuenta bancaria para ingreso:**\nES79 2100 0813 4501 2345 6789\n\n## Documentación Aportada\n\n- [x] Fotocopia DNI\n- [x] Justificante de titularidad bancaria\n- [ ] Memoria descriptiva del proyecto\n\n---\n\n**Firma del solicitante**\n\nEn Córdoba, a 15 de enero de 2024\n\n[Firma manuscrita]"
    },
    {
      "id": "DOC-002",
      "nombre": "dni.pdf",
      "fecha": "2024-01-15T08:30:00Z",
      "tipo": "IDENTIFICACION",
      "ruta": "data/documentos/EXP-2024-001/dni.pdf",
      "hash_sha256": "def456...",
      "tamano_bytes": 123456,
      "validado": null,
      "metadatos_extraidos": {
        "numero_documento": "12345678A",
        "tipo_documento": "DNI",
        "nombre_completo": "María García López",
        "apellido1": "García",
        "apellido2": "López",
        "nombre": "María",
        "fecha_nacimiento": "1985-03-15",
        "lugar_nacimiento": "Córdoba",
        "sexo": "F",
        "nacionalidad": "ESPAÑOLA",
        "fecha_expedicion": "2020-01-10",
        "fecha_caducidad": "2030-01-10",
        "equipo_expedidor": "CÓRDOBA"
      },
      "texto_markdown": "# Documento Nacional de Identidad\n\n**ESPAÑA**\n\n## Anverso\n\n| Campo | Valor |\n|-------|-------|\n| Apellidos | GARCÍA LÓPEZ |\n| Nombre | MARÍA |\n| Sexo | F |\n| Nacionalidad | ESPAÑOLA |\n| Fecha de nacimiento | 15 03 1985 |\n| Lugar de nacimiento | CÓRDOBA |\n\n## Reverso\n\n| Campo | Valor |\n|-------|-------|\n| Número | 12345678A |\n| Fecha de expedición | 10 01 2020 |\n| Válido hasta | 10 01 2030 |\n| Equipo | CÓRDOBA |\n\n---\n\n[Fotografía del titular]\n[Firma del titular]\n[Código de barras/QR]"
    },
    {
      "id": "DOC-003",
      "nombre": "justificante_bancario.pdf",
      "fecha": "2024-01-15T08:30:00Z",
      "tipo": "BANCARIO",
      "ruta": "data/documentos/EXP-2024-001/justificante.pdf",
      "hash_sha256": "ghi789...",
      "tamano_bytes": 98765,
      "validado": null,
      "metadatos_extraidos": {
        "entidad": "Banco Ejemplo S.A.",
        "codigo_entidad": "2100",
        "numero_cuenta_completo": "ES79 2100 0813 4501 2345 6789",
        "iban": "ES79",
        "tipo_cuenta": "CUENTA CORRIENTE",
        "titular": "María García López",
        "nif_titular": "12345678A",
        "fecha_certificado": "2024-01-14",
        "validez": "Este certificado tiene validez de 30 días"
      },
      "texto_markdown": "# Certificado de Titularidad Bancaria\n\n**BANCO EJEMPLO S.A.**\n\nCIF: A12345678\n\n---\n\n## Certificado\n\nD./Dña. **RESPONSABLE DE OFICINA 0813**\n\n**CERTIFICA:**\n\nQue según nuestros registros, la cuenta número:\n\n**ES79 2100 0813 4501 2345 6789**\n\nFigura a nombre de:\n\n**MARÍA GARCÍA LÓPEZ** - NIF: 12345678A\n\n| Dato | Valor |\n|------|-------|\n| Tipo de cuenta | CUENTA CORRIENTE |\n| Fecha de apertura | 15/03/2018 |\n| Estado | ACTIVA |\n\n---\n\nY para que conste y surta los efectos oportunos, se expide el presente certificado.\n\nEn Córdoba, a 14 de enero de 2024\n\n[Firma electrónica]\n[Sello de la entidad]"
    }
  ]
}
```

### Crear datos para EXP-2024-002 y EXP-2024-003

Aplicar el mismo patrón con documentos coherentes para cada tipo de expediente:

- **EXP-2024-002** (Licencia de Obras):
  - Solicitud de licencia
  - DNI/NIE del solicitante
  - Escrituras de propiedad
  - Planos del proyecto
  - Memoria técnica

- **EXP-2024-003** (Archivado):
  - Solicitud original
  - Documentación aportada
  - Resolución favorable
  - Notificación al interesado

## Tests Funcionales a Añadir

### test_tools_documents.py

```python
# ========== Tests de Lectura ==========

def test_obtener_texto_documento_existente():
    """
    Given: Un token válido y un documento con texto_markdown
    When: Se invoca obtener_texto_documento(EXP-2024-001, DOC-002)
    Then: Se retorna el texto markdown del DNI
    """

def test_obtener_texto_documento_sin_texto():
    """
    Given: Un documento sin texto_markdown
    When: Se invoca obtener_texto_documento
    Then: Se retorna error 422 "Documento sin texto disponible"
    """

def test_obtener_metadatos_documento_existente():
    """
    Given: Un documento con metadatos_extraidos
    When: Se invoca obtener_metadatos_documento(EXP-2024-001, DOC-002)
    Then: Se retorna el NIF, nombre, fechas del DNI
    """

def test_obtener_metadatos_documento_sin_metadatos():
    """
    Given: Un documento sin metadatos_extraidos
    When: Se invoca obtener_metadatos_documento
    Then: Se retorna error 422 "Documento sin metadatos extraídos"
    """

# ========== Tests de Escritura ==========

def test_actualizar_metadatos_documento_merge():
    """
    Given: Un documento con metadatos existentes
    When: Se invoca actualizar_metadatos_documento con reemplazar=false
    Then: Los nuevos metadatos se mezclan con los existentes
    """

def test_actualizar_metadatos_documento_replace():
    """
    Given: Un documento con metadatos existentes
    When: Se invoca actualizar_metadatos_documento con reemplazar=true
    Then: Los metadatos anteriores se reemplazan completamente
    """

def test_crear_documento_desde_markdown():
    """
    Given: Un token con permiso de gestión
    When: Se invoca crear_documento_desde_markdown con un informe
    Then: Se crea el documento con texto_markdown y metadatos
    And: Se registra en el historial del expediente
    """

def test_crear_documento_requiere_gestion():
    """
    Given: Un token con solo permiso de consulta
    When: Se invoca crear_documento_desde_markdown
    Then: Se retorna error 403 "Permiso insuficiente"
    """

# ========== Tests de Integración ==========

def test_flujo_validacion_documento():
    """
    Test de integración: Validación completa de un DNI

    1. Agente obtiene texto_markdown del DNI
    2. Agente obtiene metadatos_extraidos
    3. Agente verifica que el NIF del metadato coincide con el del expediente
    4. Agente actualiza metadatos con resultado de validación
    5. Agente crea informe de validación desde markdown
    """

def test_flujo_generacion_informe():
    """
    Test de integración: Generación de informe desde agente

    1. Agente consulta expediente
    2. Agente obtiene metadatos de todos los documentos
    3. Agente genera texto markdown del informe
    4. Agente crea documento desde markdown
    5. Verificar que el documento aparece en listar_documentos
    """
```

## Tareas de Implementación

### Fase 1: Modelo de Datos

- [ ] Actualizar `models.py`: Añadir campos `metadatos_extraidos` y `texto_markdown` a `Documento`
- [ ] Actualizar JSON de expedientes mock con nuevos campos
- [ ] Crear directorio `data/documentos/` con archivos markdown de ejemplo

### Fase 2: Tools de Lectura

- [ ] Implementar `obtener_texto_documento` en `tools.py`
- [ ] Implementar `obtener_metadatos_documento` en `tools.py`
- [ ] Añadir tests para tools de lectura

### Fase 3: Tools de Escritura

- [ ] Implementar `actualizar_metadatos_documento` en `tools.py`
- [ ] Implementar `crear_documento_desde_markdown` en `tools.py`
- [ ] Añadir tests para tools de escritura

### Fase 4: Tests e Integración

- [ ] Crear `tests/test_mcp/test_tools_documents.py`
- [ ] Actualizar tests existentes que dependen del modelo de Documento
- [ ] Ejecutar suite completa de tests

## Criterios de Aceptación

- [ ] Modelo `Documento` incluye `metadatos_extraidos` y `texto_markdown`
- [ ] 4 nuevas tools implementadas y documentadas
- [ ] Expedientes mock actualizados con datos realistas
- [ ] Tests funcionales completos para nuevas tools
- [ ] Validación de permisos (`gestion` para escritura)
- [ ] Historial actualizado en operaciones de escritura
- [ ] Documentación actualizada en `list_tools()`

## Referencias

- [Prompt original: make-mcp-mock.md](./make-mcp-mock.md)
- [Modelo actual: models.py](/src/mcp_mock/mcp_expedientes/models.py)
- [Tools actual: tools.py](/src/mcp_mock/mcp_expedientes/tools.py)
- [Datos mock: EXP-2024-001.json](/src/mcp_mock/mcp_expedientes/data/expedientes/EXP-2024-001.json)
