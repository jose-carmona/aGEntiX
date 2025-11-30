## Plan

1) crear esqueleto de back-office que recubra las llamadas al sistemas de agentes. En éste punto el sistema será un simple mock funcional que contemple todos los requisitos.
2) crear API con FastAPI para llamar al esqueleto back-office.
3) mejorar el esqueleto del punto 1 para convertirlo en un sistema de agentes usando LangGraph o CrewAI; el sistema será capaz de usar los dos. En este punto El sistema será capaz de consumir tools en MCP. El sistema en este punto tendrá un único worker.
4) mejorar el sistema de agentes para que pueda escalar horizontalmente con Celery + redis con diferentes workers.