"""
action_result.py - Estructura estandarizada de resultados de Computer Use y herramientas de Miku V2.

Distingue estrictamente entre:
- confirmed: Acción ejecutada e inspeccionada con evidencia verificada de éxito.
- executed_unverified: Comando emitido (ej. click o tipeo), pero sin confirmación del cambio resultante.
- failed: La acción no pudo ejecutarse o falló la verificación/herramienta.
- requires_user: La acción requiere intervención humana directa (ej. contraseñas, 2FA, pagos).
"""

from dataclasses import dataclass, field
from enum import Enum
import json
import re
from typing import Dict, Any, Optional, List

class ActionStatus(str, Enum):
    CONFIRMED = "confirmed"
    EXECUTED_UNVERIFIED = "executed_unverified"
    FAILED = "failed"
    REQUIRES_USER = "requires_user"

# Palabras clave y patrones que identifican operaciones de autenticación o datos sensibles
SENSITIVE_PATTERNS = [
    r"\b(contrase[ñn]a|password|passwd|clave)\b",
    r"\b(2fa|mfa|otp|segundo factor|c[oó]digo de verificaci[oó]n|token de seguridad)\b",
    r"\b(pin|cvv|tarjeta de cr[eé]dito|tarjeta de d[eé]bito)\b",
    r"\b(iniciar sesi[oó]n|login|sign in|autenticaci[oó]n)\b",
    r"\b(credencial(es)?|api[_-]?key|secret[_-]?key)\b",
    r"\b(confirmar pago|autorizar pago|transferir dinero)\b",
    r"\b(uac|control de cuentas de usuario|permiso de administrador)\b"
]

def check_sensitive_action(intent: str = "", target: str = "", text: str = "") -> Optional[str]:
    """
    Verifica si una intención, elemento de destino o texto a escribir involucra credenciales
    o pasos de autenticación sensibles que requieran intervención humana obligatoria.
    Devuelve la razón si es sensible, o None si no lo es.
    """
    combined = f"{intent} {target} {text}".lower()
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            return (
                "Operación sensible detectada (credenciales, contraseña, segundo factor o autorización). "
                "Por políticas de seguridad, Miku se detiene y requiere que ingreses o confirmes estos datos directamente."
            )
    return None

@dataclass
class ActionResult:
    status: str  # ActionStatus value
    action: str  # 'click', 'click_visual', 'type', 'scan', 'scroll', 'move_visual', etc.
    target: str = ""
    evidence: str = ""
    error: Optional[str] = None
    requires_user_reason: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def is_confirmed(self) -> bool:
        return self.status == ActionStatus.CONFIRMED.value

    def is_unverified(self) -> bool:
        return self.status == ActionStatus.EXECUTED_UNVERIFIED.value

    def is_failed(self) -> bool:
        return self.status == ActionStatus.FAILED.value

    def requires_user(self) -> bool:
        return self.status == ActionStatus.REQUIRES_USER.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "action": self.action,
            "target": self.target,
            "evidence": self.evidence,
            "error": self.error,
            "requires_user_reason": self.requires_user_reason,
            "data": self.data
        }

    def to_agent_string(self) -> str:
        """Formato claro y estructurado para ser consumido por el LLM en su historial."""
        lines = [
            "[RESULTADO DE ACCIÓN]",
            f"Estado: {self.status.upper()}",
            f"Acción: {self.action}"
        ]
        if self.target:
            lines.append(f"Objetivo: {self.target}")
        if self.evidence:
            lines.append(f"Evidencia: {self.evidence}")
        if self.error:
            lines.append(f"Error: {self.error}")
        if self.requires_user_reason:
            lines.append(f"Intervención requerida: {self.requires_user_reason}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_agent_string()

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ActionResult":
        return cls(
            status=d.get("status", ActionStatus.FAILED.value),
            action=d.get("action", "unknown"),
            target=d.get("target", ""),
            evidence=d.get("evidence", ""),
            error=d.get("error"),
            requires_user_reason=d.get("requires_user_reason"),
            data=d.get("data", {})
        )

    @classmethod
    def parse(cls, raw: Any) -> "ActionResult":
        """Convierte cualquier salida de herramienta en un ActionResult consistente."""
        if isinstance(raw, ActionResult):
            return raw
        if isinstance(raw, dict) and "status" in raw:
            return cls.from_dict(raw)
        
        raw_str = str(raw or "")
        # Parsear si contiene el bloque formateado
        if "[RESULTADO DE ACCIÓN]" in raw_str:
            status = ActionStatus.EXECUTED_UNVERIFIED.value
            action = "unknown"
            target = ""
            evidence = ""
            error = None
            req_user = None

            for line in raw_str.splitlines():
                line = line.strip()
                if line.startswith("Estado:"):
                    val = line.split(":", 1)[1].strip().lower()
                    if val in [s.value for s in ActionStatus]:
                        status = val
                elif line.startswith("Acción:"):
                    action = line.split(":", 1)[1].strip()
                elif line.startswith("Objetivo:"):
                    target = line.split(":", 1)[1].strip()
                elif line.startswith("Evidencia:"):
                    evidence = line.split(":", 1)[1].strip()
                elif line.startswith("Error:"):
                    error = line.split(":", 1)[1].strip()
                elif line.startswith("Intervención requerida:"):
                    req_user = line.split(":", 1)[1].strip()

            return cls(
                status=status,
                action=action,
                target=target,
                evidence=evidence,
                error=error,
                requires_user_reason=req_user
            )

        # Heurísticas de seguridad para strings heredados
        low = raw_str.lower()
        if any(w in low for w in ["denegada", "bloqueada", "error", "falló", "fallo", "no se encontró", "invalid"]):
            return cls(
                status=ActionStatus.FAILED.value,
                action="tool",
                error=raw_str
            )
        if "verificado con éxito" in low:
            return cls(
                status=ActionStatus.CONFIRMED.value,
                action="tool",
                evidence=raw_str
            )
        
        # Cualquier otra acción ejecutada sin evidencia explícita de confirmación es unverified
        return cls(
            status=ActionStatus.EXECUTED_UNVERIFIED.value,
            action="tool",
            evidence=raw_str
        )
