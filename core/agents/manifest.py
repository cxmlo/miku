"""AgentManifest schema, phase fallbacks, and validation for Miku."""
from dataclasses import dataclass, field, asdict
from typing import Literal, Tuple, List, Dict, Any, Optional
import re

RoleType = Literal["code", "research", "data", "general"]
CliPermissionLevel = Literal["read_only", "workspace_write", "full_terminal"]

ROLE_PHASE_FALLBACKS: Dict[str, Tuple[str, str, str, str]] = {
    "code": ("Read", "Edit", "Bash", "Done"),
    "research": ("Search", "Extract", "Synthesize", "Done"),
    "data": ("Scan", "Process", "Write", "Done"),
    "general": ("Listen", "Think", "Action", "Done")
}

def generate_vault_key_var(agent_name: str) -> str:
    """Generate deterministic environment variable name for the vault key."""
    clean = re.sub(r"[^A-Za-z0-9]+", "_", agent_name.strip()).upper().strip("_")
    return f"MIKU_AGENT_{clean or 'DEFAULT'}_KEY"

@dataclass
class AgentManifest:
    id: str
    name: str
    role: str
    role_type: RoleType = "code"
    phases: Tuple[str, str, str, str] = field(default=("Read", "Edit", "Bash", "Done"))
    permissions: CliPermissionLevel = "workspace_write"
    model_id: str = "deepseek-chat"
    vault_key_var: str = ""
    system_prompt: str = ""
    temperature: float = 0.2
    skills: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)
    color: str = "#00f0ff"
    outfit: str = "default"
    memory_isolated: bool = True

    def __post_init__(self):
        # Normalize and validate role_type
        if self.role_type not in ROLE_PHASE_FALLBACKS:
            self.role_type = "general"

        # Apply deterministic phase fallback if phases is missing or invalid
        if not self.phases or len(self.phases) != 4 or not all(isinstance(p, str) and p.strip() for p in self.phases):
            self.phases = ROLE_PHASE_FALLBACKS[self.role_type]
        else:
            self.phases = tuple(p.strip() for p in self.phases)

        # Normalize permissions
        valid_perms = {"read_only", "workspace_write", "full_terminal"}
        if self.permissions not in valid_perms:
            self.permissions = "workspace_write"

        # Auto-generate vault key var if blank
        if not self.vault_key_var:
            self.vault_key_var = generate_vault_key_var(self.name or self.id)

        # Clamp temperature
        if self.temperature is None:
            self.temperature = 0.2 if self.role_type == "code" else 0.7
        else:
            self.temperature = max(0.0, min(1.0, float(self.temperature)))

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["phases"] = list(self.phases)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentManifest":
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        name = str(data.get("name", "Unnamed Agent")).strip()
        slug = str(data.get("id", "")).strip() or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        role = str(data.get("role", "Assistant")).strip()
        role_type = data.get("role_type", "general")
        if role_type not in ROLE_PHASE_FALLBACKS:
            role_type = "general"

        raw_phases = data.get("phases")
        if raw_phases and isinstance(raw_phases, (list, tuple)) and len(raw_phases) == 4:
            phases = tuple(str(p).strip() for p in raw_phases)
        else:
            phases = ROLE_PHASE_FALLBACKS[role_type]

        return cls(
            id=slug,
            name=name,
            role=role,
            role_type=role_type,
            phases=phases,
            permissions=data.get("permissions", "workspace_write"),
            model_id=str(data.get("model_id", "deepseek-chat")).strip(),
            vault_key_var=str(data.get("vault_key_var", "")).strip() or generate_vault_key_var(name),
            system_prompt=str(data.get("system_prompt", "")),
            temperature=float(data.get("temperature", 0.2 if role_type == "code" else 0.7)),
            skills=list(data.get("skills", [])),
            mcp_servers=list(data.get("mcp_servers", [])),
            color=str(data.get("color", "#00f0ff")),
            outfit=str(data.get("outfit", "default")),
            memory_isolated=bool(data.get("memory_isolated", True))
        )
