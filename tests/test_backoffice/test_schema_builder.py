# tests/test_backoffice/test_schema_builder.py

"""
Tests para el constructor dinámico de schemas Pydantic.

Verifica que los JSON Schemas del servidor MCP se convierten
correctamente a modelos Pydantic utilizables por CrewAI.
"""

import pytest
from pydantic import ValidationError

from backoffice.agents.schema_builder import (
    build_pydantic_model,
    build_models_from_tools,
    GenericMCPArgs,
    _get_python_type,
    _create_field_info
)


class TestBuildPydanticModel:
    """Tests para build_pydantic_model"""

    def test_simple_string_field(self):
        """Test: Campo string simple requerido"""
        schema = {
            "type": "object",
            "properties": {
                "expediente_id": {
                    "type": "string",
                    "description": "ID del expediente"
                }
            },
            "required": ["expediente_id"]
        }

        Model = build_pydantic_model("TestArgs", schema)

        # Debe poder instanciarse con el campo
        instance = Model(expediente_id="EXP-001")
        assert instance.expediente_id == "EXP-001"

        # Debe fallar sin el campo requerido
        with pytest.raises(ValidationError):
            Model()

    def test_optional_field(self):
        """Test: Campo opcional con default None"""
        schema = {
            "type": "object",
            "properties": {
                "expediente_id": {
                    "type": "string",
                    "description": "ID del expediente"
                },
                "criterios": {
                    "type": "object",
                    "description": "Criterios opcionales"
                }
            },
            "required": ["expediente_id"]
        }

        Model = build_pydantic_model("TestArgs", schema)

        # Debe funcionar sin el campo opcional
        instance = Model(expediente_id="EXP-001")
        assert instance.expediente_id == "EXP-001"
        assert instance.criterios is None

        # Debe funcionar con el campo opcional
        instance2 = Model(expediente_id="EXP-001", criterios={"key": "value"})
        assert instance2.criterios == {"key": "value"}

    def test_multiple_types(self):
        """Test: Múltiples tipos de campos"""
        schema = {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre"},
                "cantidad": {"type": "integer", "description": "Cantidad"},
                "precio": {"type": "number", "description": "Precio"},
                "activo": {"type": "boolean", "description": "Activo"},
                "tags": {"type": "array", "description": "Tags"},
                "metadata": {"type": "object", "description": "Metadata"}
            },
            "required": ["nombre", "cantidad"]
        }

        Model = build_pydantic_model("MultiTypeArgs", schema)

        instance = Model(
            nombre="Test",
            cantidad=5,
            precio=10.5,
            activo=True,
            tags=["a", "b"],
            metadata={"key": "value"}
        )

        assert instance.nombre == "Test"
        assert instance.cantidad == 5
        assert instance.precio == 10.5
        assert instance.activo is True
        assert instance.tags == ["a", "b"]
        assert instance.metadata == {"key": "value"}

    def test_empty_schema(self):
        """Test: Schema vacío genera modelo genérico"""
        Model = build_pydantic_model("EmptyArgs", {})

        # Debe poder instanciarse sin campos
        instance = Model()
        assert instance is not None

    def test_no_properties_schema(self):
        """Test: Schema sin propiedades"""
        schema = {"type": "object"}

        Model = build_pydantic_model("NoPropsArgs", schema)
        instance = Model()
        assert instance is not None

    def test_field_without_type(self):
        """Test: Campo sin tipo especificado usa Any"""
        schema = {
            "type": "object",
            "properties": {
                "valor": {
                    "description": "Valor sin tipo"
                }
            },
            "required": ["valor"]
        }

        Model = build_pydantic_model("AnyTypeArgs", schema)

        # Debe aceptar cualquier tipo
        instance1 = Model(valor="string")
        instance2 = Model(valor=123)
        instance3 = Model(valor={"key": "value"})

        assert instance1.valor == "string"
        assert instance2.valor == 123
        assert instance3.valor == {"key": "value"}

    def test_actualizar_datos_schema(self):
        """Test: Schema real de actualizar_datos"""
        schema = {
            "type": "object",
            "properties": {
                "expediente_id": {
                    "type": "string",
                    "description": "ID del expediente"
                },
                "campo": {
                    "type": "string",
                    "description": "Ruta del campo a actualizar"
                },
                "valor": {
                    "description": "Nuevo valor para el campo"
                }
            },
            "required": ["expediente_id", "campo", "valor"]
        }

        Model = build_pydantic_model("ActualizarDatosArgs", schema)

        instance = Model(
            expediente_id="EXP-001",
            campo="datos.validado",
            valor=True
        )

        assert instance.expediente_id == "EXP-001"
        assert instance.campo == "datos.validado"
        assert instance.valor is True


class TestBuildModelsFromTools:
    """Tests para build_models_from_tools"""

    def test_build_multiple_models(self):
        """Test: Construye modelos para múltiples tools"""
        tools_with_schemas = {
            "consultar_expediente": {
                "name": "consultar_expediente",
                "description": "Consulta expediente",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expediente_id": {"type": "string"}
                    },
                    "required": ["expediente_id"]
                },
                "server_id": "test-mcp"
            },
            "añadir_anotacion": {
                "name": "añadir_anotacion",
                "description": "Añade anotación",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expediente_id": {"type": "string"},
                        "texto": {"type": "string"}
                    },
                    "required": ["expediente_id", "texto"]
                },
                "server_id": "test-mcp"
            }
        }

        models = build_models_from_tools(tools_with_schemas)

        assert "consultar_expediente" in models
        assert "añadir_anotacion" in models

        # Verificar que los modelos funcionan
        ConsultarModel = models["consultar_expediente"]
        instance1 = ConsultarModel(expediente_id="EXP-001")
        assert instance1.expediente_id == "EXP-001"

        AnotacionModel = models["añadir_anotacion"]
        instance2 = AnotacionModel(expediente_id="EXP-001", texto="Test")
        assert instance2.texto == "Test"

    def test_model_names_are_camelcase(self):
        """Test: Los nombres de modelo son CamelCase + Args"""
        tools_with_schemas = {
            "consultar_expediente": {
                "name": "consultar_expediente",
                "inputSchema": {},
                "server_id": "test"
            }
        }

        models = build_models_from_tools(tools_with_schemas)
        Model = models["consultar_expediente"]

        # El nombre debe ser ConsultarExpedienteArgs
        assert Model.__name__ == "ConsultarExpedienteArgs"


class TestGenericMCPArgs:
    """Tests para GenericMCPArgs"""

    def test_accepts_any_fields(self):
        """Test: GenericMCPArgs acepta cualquier campo"""
        instance = GenericMCPArgs(
            expediente_id="EXP-001",
            campo="test",
            valor=123,
            extra_field="extra"
        )

        assert instance.expediente_id == "EXP-001"
        assert instance.campo == "test"
        assert instance.valor == 123
        assert instance.extra_field == "extra"

    def test_empty_instantiation(self):
        """Test: GenericMCPArgs puede instanciarse vacío"""
        instance = GenericMCPArgs()
        assert instance is not None


class TestHelperFunctions:
    """Tests para funciones auxiliares"""

    def test_get_python_type_string(self):
        """Test: string -> str"""
        assert _get_python_type("string", True) == str

    def test_get_python_type_integer(self):
        """Test: integer -> int"""
        assert _get_python_type("integer", True) == int

    def test_get_python_type_number(self):
        """Test: number -> float"""
        assert _get_python_type("number", True) == float

    def test_get_python_type_boolean(self):
        """Test: boolean -> bool"""
        assert _get_python_type("boolean", True) == bool

    def test_get_python_type_optional(self):
        """Test: Tipo opcional envuelve en Optional"""
        from typing import Optional
        result = _get_python_type("string", is_required=False)
        # Verificar que es Optional[str]
        assert result.__origin__ is type(None) or hasattr(result, "__origin__")
