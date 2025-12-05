# backoffice/logging/pii_redactor.py

import re
from typing import Dict, Pattern


class PIIRedactor:
    """
    Redacta automáticamente información personal identificable (PII).

    Cumplimiento: GDPR Art. 32, LOPD, ENS
    """

    # Patrones de redacción
    PATTERNS: Dict[str, Pattern] = {
        "dni": re.compile(r'\b\d{8}[A-Z]\b'),
        "nie": re.compile(r'\b[XYZ]\d{7}[A-Z]\b'),
        "email": re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'),
        "telefono": re.compile(r'\b[6-9]\d{8}\b'),
        "iban": re.compile(r'\bES\d{22}\b'),
        "tarjeta": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        "ccc": re.compile(r'\b\d{20}\b'),  # Código Cuenta Cliente
    }

    @classmethod
    def redact(cls, text: str) -> str:
        """
        Redacta todos los patrones de PII en el texto.

        Args:
            text: Texto que puede contener PII

        Returns:
            Texto con PII redactada

        Examples:
            >>> PIIRedactor.redact("DNI: 12345678A")
            'DNI: [DNI-REDACTED]'
            >>> PIIRedactor.redact("Email: juan@example.com")
            'Email: [EMAIL-REDACTED]'
        """
        redacted = text
        for pii_type, pattern in cls.PATTERNS.items():
            redacted = pattern.sub(f'[{pii_type.upper()}-REDACTED]', redacted)
        return redacted
