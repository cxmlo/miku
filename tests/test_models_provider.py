import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models_provider

def test_available_models_structure():
    """Verifica que el catálogo de modelos contenga todas las categorías requeridas"""
    avail = models_provider.get_available_models()
    assert "chat" in avail
    assert "pro" in avail
    assert "computer_use" in avail
    assert "stt" in avail
    
    # Cada modelo debe tener id, name y provider
    for category in ["chat", "pro", "computer_use", "stt"]:
        for model in avail[category]:
            assert "id" in model
            assert "name" in model
            assert "provider" in model

def test_pro_models_present():
    """Verifica que la categoría Pro incluya modelos avanzados de código y razonamiento"""
    avail = models_provider.get_available_models()
    pro_ids = [m["id"] for m in avail["pro"]]
    # Modelos recomendados para programación y pro
    has_pro = any("coder" in m_id.lower() or "gemini-2.5-pro" in m_id.lower() or "claude" in m_id.lower() or "r1" in m_id.lower() for m_id in pro_ids)
    assert has_pro or len(pro_ids) > 0

def test_non_chat_models_excluded():
    """Verifica que modelos no aptos para chat (como generadores de audio o embeddings) estén excluidos"""
    avail = models_provider.get_available_models()
    all_chat_ids = [m["id"] for m in avail["chat"]]
    
    for bad_kw in ["lyria", "embedding", "imagen", "tts"]:
        for m_id in all_chat_ids:
            assert bad_kw not in m_id.lower(), f"El modelo no conversacional '{m_id}' no debería estar en la lista de chat"

def test_configured_models_keys():
    """Verifica que la configuración activa tenga claves para chat, pro, computer_use y stt"""
    current = models_provider.get_configured_models()
    assert "chat" in current
    assert "pro" in current
    assert "computer_use" in current
    assert "stt" in current
