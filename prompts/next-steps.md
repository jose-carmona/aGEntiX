## Plan

1) crear esqueleto de back-office que recubra las llamadas al sistemas de agentes. En éste punto el sistema será un simple mock funcional que contemple todos los requisitos. OK
2) crear API con FastAPI para llamar al esqueleto back-office.
3) para la demostración (se trata de un proyecto Captson de final de curso) el sistema contará con un pequeño frontend aparte con las siguiente funcionalidades:
    * muestre la métricas más importantes del sistema
    * muestre los logs del sistema
    * permita invocar un agente a modo de Test
4) Refinar el concepto de "agente" y como se invoca. Se trata de simplificar la invocación.
5) Es el momento de revisar la documentación del proyecto y que todos los elementos están correctamente enfocados.
6) mejorar el esqueleto del punto 1 para convertirlo en un sistema de agentes usando LangGraph o CrewAI; el sistema será capaz de usar los dos. En este punto El sistema será capaz de consumir tools en MCP. El sistema en este punto tendrá un único worker.
7) mejorar el sistema de agentes para que pueda escalar horizontalmente con Celery + redis con diferentes workers.