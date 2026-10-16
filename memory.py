import json
import os
import uuid
import chromadb
from chromadb.config import Settings
from miku_paths import get_miku_data_dir

# Directorio de la BD vectorial en APPDATA
DB_PATH = os.path.join(get_miku_data_dir(), "db")
os.makedirs(DB_PATH, exist_ok=True)

try:
    db_client = chromadb.PersistentClient(
        path=DB_PATH,
        settings=Settings(anonymized_telemetry=False, is_persistent=True)
    )
    user_facts_collection = db_client.get_or_create_collection(name="user_facts")
    links_collection = db_client.get_or_create_collection(name="saved_links")
except Exception as e:
    print(f"[WARN] Error inicializando ChromaDB en {DB_PATH}: {e}")
    db_client = None
    user_facts_collection = None
    links_collection = None

MEMORY_FILE = "miku_memory.json"
LINKS_FILE = "miku_links.json"

def _migrate_old_data():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memories = json.load(f)
            for i, m in enumerate(memories):
                user_facts_collection.upsert(documents=[m], ids=[f"old_mem_{i}_{uuid.uuid4().hex[:6]}"])
            os.rename(MEMORY_FILE, MEMORY_FILE + ".migrated")
        except Exception as e:
            print("Error migrando memorias:", e)

    if os.path.exists(LINKS_FILE):
        try:
            with open(LINKS_FILE, "r", encoding="utf-8") as f:
                links = json.load(f)
            for i, link in enumerate(links):
                links_collection.upsert(
                    documents=[link["contexto"]],
                    metadatas=[{"url": link["url"]}],
                    ids=[f"old_link_{i}_{uuid.uuid4().hex[:6]}"]
                )
            os.rename(LINKS_FILE, LINKS_FILE + ".migrated")
        except Exception as e:
            print("Error migrando enlaces:", e)

# Ejecutar migración una sola vez
_migrate_old_data()

def add_memory(fact: str) -> str:
    if not user_facts_collection:
        return "Memoria no disponible temporalmente."
    doc_id = str(uuid.uuid4())
    user_facts_collection.add(documents=[fact], ids=[doc_id])
    return f"Dato guardado en la memoria vectorial: '{fact}'"

def guardar_enlace(contexto: str, url: str) -> str:
    if not links_collection:
        return "Memoria no disponible temporalmente."
    doc_id = str(uuid.uuid4())
    links_collection.add(documents=[contexto], metadatas=[{"url": url}], ids=[doc_id])
    return f"Enlace guardado en memoria vectorial: {contexto} -> {url}"

def get_all_memories() -> str:
    if not user_facts_collection:
        return "No hay memorias guardadas aún."
    results = user_facts_collection.get()
    if not results or not results["documents"]:
        return "No hay memorias guardadas aún."
    return "Memorias sobre el usuario:\n" + "\n".join(f"- {doc}" for doc in results["documents"])

def get_all_links() -> str:
    if not links_collection:
        return ""
    results = links_collection.get()
    if not results or not results["documents"]:
        return ""
    docs = results["documents"]
    metas = results["metadatas"]
    return "Colección de Enlaces guardados:\n" + "\n".join(f"- {docs[i]}: {metas[i]['url']}" for i in range(len(docs)))

def buscar_en_memoria(consulta: str, tipo: str = "ambos", n_results: int = 4) -> str:
    """Busca en la base de datos vectorial usando similitud semántica."""
    resultados = []
    
    if tipo in ["ambos", "usuario"] and user_facts_collection and user_facts_collection.count() > 0:
        try:
            res_user = user_facts_collection.query(
                query_texts=[consulta],
                n_results=min(n_results, user_facts_collection.count())
            )
            if res_user and res_user["documents"] and res_user["documents"][0]:
                resultados.append("--- Recuerdos sobre el usuario ---")
                for i, doc in enumerate(res_user["documents"][0]):
                    dist = res_user["distances"][0][i]
                    resultados.append(f"- {doc} (Similitud: {dist:.2f})")
        except Exception as e:
            print("Error en búsqueda de usuario:", e)
            
    if tipo in ["ambos", "enlaces"] and links_collection and links_collection.count() > 0:
        try:
            res_links = links_collection.query(
                query_texts=[consulta],
                n_results=min(n_results, links_collection.count())
            )
            if res_links and res_links["documents"] and res_links["documents"][0]:
                resultados.append("--- Enlaces guardados ---")
                for i, doc in enumerate(res_links["documents"][0]):
                    meta = res_links["metadatas"][0][i]
                    dist = res_links["distances"][0][i]
                    resultados.append(f"- Contexto: {doc} | URL: {meta['url']} (Similitud: {dist:.2f})")
        except Exception as e:
            print("Error en búsqueda de enlaces:", e)
            
    if not resultados:
        return f"No se encontraron resultados relevantes en la memoria semántica para: '{consulta}'"
        
    return "\n".join(resultados)
