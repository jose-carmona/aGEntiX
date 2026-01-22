# backoffice/tasks/__init__.py

"""
Paquete de tareas Celery para aGEntiX.

Este paquete contiene las tareas Celery que se ejecutan en workers
distribuidos para procesamiento de agentes.

Tareas disponibles:
- execute_agent_task: Ejecuta un agente de forma asíncrona
"""

from .agent_execution import execute_agent_task

__all__ = ['execute_agent_task']
