"""Miku Agents Module: Manifest, Bus, Memory, and Manager."""

from core.agents.manifest import (
    AgentManifest,
    RoleType,
    CliPermissionLevel,
    ROLE_PHASE_FALLBACKS,
    generate_vault_key_var,
)
from core.agents.bus import AgentBus, DelegationEvent, agent_bus
from core.agents.memory import AgentMemory, MemoryManager, memory_manager
from core.agents.manager import AgentManager, BUILTIN_AGENTS, agent_manager

__all__ = [
    "AgentManifest",
    "RoleType",
    "CliPermissionLevel",
    "ROLE_PHASE_FALLBACKS",
    "generate_vault_key_var",
    "AgentBus",
    "DelegationEvent",
    "agent_bus",
    "AgentMemory",
    "MemoryManager",
    "memory_manager",
    "AgentManager",
    "BUILTIN_AGENTS",
    "agent_manager",
]

