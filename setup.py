# setup.py

"""
Setup configuration for aGEntiX project.
Allows installing in editable mode for proper module discovery.
"""

from setuptools import setup, find_packages

setup(
    name="agentix",
    version="1.0.0",
    description="AI Agent System for GEX document management",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    install_requires=[
        "anthropic>=0.39.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "pyjwt>=2.8.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.25.0",
        "pyyaml>=6.0",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "python-multipart>=0.0.6",
        "prometheus-client>=0.19.0",
        "prometheus-fastapi-instrumentator>=6.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
        ]
    },
)
