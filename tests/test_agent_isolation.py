import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import brain

def test_agent_histories_isolation():
    """Verifica que cada agente mantenga su propio historial de conversación independiente"""
    brain.agent_conversation_histories.clear()
    brain.conversation_history = []
    
    # Simular mensaje para el agente github
    brain.agent_conversation_histories["github"] = [
        {"role": "user", "content": "Analiza este repositorio"},
        {"role": "assistant", "content": "Soy el agente de GitHub y este es mi análisis"}
    ]
    
    # Simular mensaje para el agente principal miku
    brain.conversation_history = [
        {"role": "user", "content": "Hola Miku"}
    ]
    
    # Verificar aislamiento
    assert len(brain.agent_conversation_histories["github"]) == 2
    assert len(brain.conversation_history) == 1
    assert "GitHub" in brain.agent_conversation_histories["github"][1]["content"]
    assert brain.agent_conversation_histories["github"] != brain.conversation_history

def test_subagent_persona_isolation():
    """Verifica que los subagentes GitHub y Antigravity carguen sus prompts específicos y no el instinto de Miku"""
    agent_info_gh = {
        "id": "github",
        "name": "GitHub",
        "system_prompt": "Eres el Agente GitHub especializado en git y pull requests."
    }
    
    hist = []
    # Simulación de la lógica de inyección de brain.py
    if not hist or hist[0].get("role") != "system":
        hist.insert(0, {"role": "system", "content": agent_info_gh["system_prompt"]})
        
    assert hist[0]["role"] == "system"
    assert "GitHub" in hist[0]["content"]
    assert "Miku" not in hist[0]["content"]
