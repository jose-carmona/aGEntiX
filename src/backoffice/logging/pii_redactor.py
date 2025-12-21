# backoffice/logging/pii_redactor.py

import re
import logging
from typing import Dict, Pattern

logger = logging.getLogger(__name__)


class PIIRedactor:
    """
    Redacta automáticamente información personal identificable (PII).

    Cumplimiento: GDPR Art. 32, LOPD, ENS
    """

    # Patrones de redacción
    # NOTA: El orden importa - los más específicos primero para evitar solapamiento
    PATTERNS: Dict[str, Pattern] = {
        "dni": re.compile(r'\b\d{8}[A-Z]\b'),
        "nie": re.compile(r'\b[XYZ]\d{7}[A-Z]\b'),
        "email": re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'),
        "telefono_fijo": re.compile(r'\b[89]\d{8}\b'),  # Fijos: 8 (900/800) y 9 (9XX) - ANTES que móviles
        "telefono_movil": re.compile(r'\b[67]\d{8}\b'),  # Móviles: solo 6 y 7
        "iban": re.compile(r'\bES\d{22}\b'),
        "tarjeta": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        "ccc": re.compile(r'\b\d{20}\b'),  # Código Cuenta Cliente
    }

    @classmethod
    def redact(cls, text: str) -> str:
        """
        Redacta todos los patrones de PII en el texto.

        Maneja casos edge:
        - None input → "[REDACTION-FAILED: None input]"
        - Bytes input → intenta decode UTF-8, fallback a error
        - Tipo inválido → "[REDACTION-FAILED: {tipo}]"
        - Exception durante redacción → "[REDACTION-FAILED]"

        Args:
            text: Texto que puede contener PII

        Returns:
            Texto con PII redactada o mensaje de error

        Examples:
            >>> PIIRedactor.redact("DNI: 12345678A")
            'DNI: [DNI-REDACTED]'
            >>> PIIRedactor.redact("Email: juan@example.com")
            'Email: [EMAIL-REDACTED]'
            >>> PIIRedactor.redact(None)
            '[REDACTION-FAILED: None input]'
        """
        try:
            # Validar None
            if text is None:
                logger.warning("PII redaction recibió None")
                return "[REDACTION-FAILED: None input]"

            # Validar bytes - intentar decode
            if isinstance(text, bytes):
                try:
                    text = text.decode('utf-8')
                except UnicodeDecodeError as e:
                    logger.warning(f"Failed to decode bytes for PII redaction: {e}")
                    return "[REDACTION-FAILED: invalid encoding]"

            # Validar tipo string
            if not isinstance(text, str):
                logger.warning(f"Invalid type for PII redaction: {type(text)}")
                return f"[REDACTION-FAILED: {type(text).__name__}]"

            # Redacción normal
            redacted = text
            for pii_type, pattern in cls.PATTERNS.items():
                redacted = pattern.sub(f'[{pii_type.upper()}-REDACTED]', redacted)
            return redacted

        except Exception as e:
            logger.warning(f"PII redaction failed: {type(e).__name__}: {e}")
            return "[REDACTION-FAILED]"
