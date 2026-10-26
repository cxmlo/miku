import os
import json
import asyncio
import logging
from typing import Dict, Any, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult

logger = logging.getLogger("MCPManager")

from miku_paths import get_mcp_config_path

class MikuMCPManager:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or get_mcp_config_path()
        self.servers_config = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.tools_schema_extension = []
        self.tool_routing_map = {}
        self.main_loop = None
        self.server_tasks = {}

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.servers_config = data.get("servidores", {})
                logger.info(f"Configuración MCP cargada: {len(self.servers_config)} servidores.")
            except Exception as e:
                logger.error(f"Error al leer {self.config_path}: {e}")
        else:
            logger.info("No se encontró mcp_config.json. MCP estará deshabilitado hasta que se configure.")

    async def _run_server(self, server_name: str, command: str, args: List[str]):
        try:
            import sys
            import shutil
            if sys.platform == "win32" and command in ["npx", "npm"]:
                command = command + ".cmd"
            elif command == "python":
                command = sys.executable
            else:
                # Si es un comando como mcp-server-sqlite, buscarlo en el mismo directorio de sys.executable (venv/Scripts)
                venv_scripts = os.path.dirname(sys.executable)
                possible_path = os.path.join(venv_scripts, command + (".exe" if sys.platform == "win32" and not command.endswith(".exe") else ""))
                if os.path.exists(possible_path):
                    command = possible_path
                else:
                    resolved = shutil.which(command)
                    if resolved:
                        command = resolved
                
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env={**os.environ}
            )
            
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    self.sessions[server_name] = session
                    
                    logger.info(f"Conectado exitosamente al servidor MCP: {server_name}")
                    
                    response = await session.list_tools()
                    for tool in response.tools:
                        namespaced_tool_name = f"mcp_{server_name}_{tool.name}"
                        gemini_tool = {
                            "type": "function",
                            "function": {
                                "name": namespaced_tool_name,
                                "description": tool.description or f"Herramienta MCP '{tool.name}' del servidor {server_name}.",
                                "parameters": tool.input_schema
                            }
                        }
                        # Evitar duplicados si se reconecta
                        if not any(t["function"]["name"] == namespaced_tool_name for t in self.tools_schema_extension):
                            self.tools_schema_extension.append(gemini_tool)
                        self.tool_routing_map[namespaced_tool_name] = (server_name, tool.name)
                        
                    logger.info(f"Servidor {server_name} registró {len(response.tools)} herramientas.")
                    
                    # Keep alive forever
                    await asyncio.Event().wait()
                    
        except asyncio.CancelledError:
            logger.info(f"Servidor MCP {server_name} fue cerrado correctamente.")
        except Exception as e:
            logger.error(f"Error conectando al servidor MCP {server_name}: {e}")
        finally:
            self.sessions.pop(server_name, None)

    async def connect_all(self):
        self.load_config()
        if not self.servers_config:
            return

        for server_name, config in self.servers_config.items():
            if not config.get("enabled", True):
                logger.info(f"Servidor MCP '{server_name}' omitido al inicio (deshabilitado en configuración para ahorrar tokens).")
                continue
            command = config.get("command")
            args = config.get("args", [])
            if not command:
                continue

            task = asyncio.create_task(self._run_server(server_name, command, args))
            self.server_tasks[server_name] = task

    async def toggle_server(self, server_name: str, enabled: bool) -> bool:
        """Activa o desactiva dinámicamente un servidor MCP y libera sus herramientas del contexto."""
        try:
            self.load_config()
            if server_name not in self.servers_config:
                logger.warning(f"No se puede alternar el servidor MCP '{server_name}': no existe en la configuración.")
                return False

            self.servers_config[server_name]["enabled"] = enabled
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"servidores": self.servers_config}, f, indent=2, ensure_ascii=False)

            if enabled:
                # Si no está en ejecución, iniciarlo
                if server_name not in self.server_tasks or self.server_tasks[server_name].done():
                    srv = self.servers_config[server_name]
                    task = asyncio.create_task(self._run_server(server_name, srv.get("command"), srv.get("args", [])))
                    self.server_tasks[server_name] = task
                    logger.info(f"Servidor MCP '{server_name}' activado dinámicamente.")
            else:
                # Desactivar y limpiar procesos y herramientas
                if server_name in self.server_tasks:
                    self.server_tasks[server_name].cancel()
                    del self.server_tasks[server_name]
                self.sessions.pop(server_name, None)
                self.tools_schema_extension = [t for t in self.tools_schema_extension if not t["function"]["name"].startswith(f"mcp_{server_name}_")]
                self.tool_routing_map = {k: v for k, v in self.tool_routing_map.items() if v[0] != server_name}
                logger.info(f"Servidor MCP '{server_name}' desactivado. Herramientas removidas del contexto del LLM.")

            return True
        except Exception as e:
            logger.error(f"Error alternando servidor MCP '{server_name}': {e}")
            return False

    async def add_server(self, server_name: str, command: str, args: List[str]) -> str:
        """Añade un nuevo servidor al json y lo conecta en tiempo real sin reiniciar."""
        try:
            self.load_config()
            self.servers_config[server_name] = {"command": command, "args": args, "enabled": True}
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"servidores": self.servers_config}, f, indent=2, ensure_ascii=False)
                
            task = asyncio.create_task(self._run_server(server_name, command, args))
            self.server_tasks[server_name] = task
            
            # Wait for connection (up to 60 seconds because npx downloads take time)
            for _ in range(600): # up to 60 seconds
                if server_name in self.sessions:
                    return f"Servidor {server_name} instalado y conectado con éxito."
                await asyncio.sleep(0.1)
                
            return f"Error al instalar el servidor MCP {server_name}: El proceso tardó demasiado en inicializar o falló en segundo plano."
            
        except Exception as e:
            return f"Error al instalar el servidor MCP {server_name}: {e}"

    async def remove_server(self, server_name: str) -> bool:
        """Elimina un servidor del json y lo detiene en tiempo real."""
        try:
            self.load_config()
            if server_name in self.servers_config:
                del self.servers_config[server_name]
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump({"servidores": self.servers_config}, f, indent=2, ensure_ascii=False)
            
            # Detener la tarea
            if server_name in self.server_tasks:
                self.server_tasks[server_name].cancel()
                del self.server_tasks[server_name]
            
            # Limpiar herramientas
            self.tools_schema_extension = [t for t in self.tools_schema_extension if not t["function"]["name"].startswith(f"mcp_{server_name}_")]
            self.tool_routing_map = {k: v for k, v in self.tool_routing_map.items() if v[0] != server_name}
            
            return True
        except Exception as e:
            logger.error(f"Error al eliminar MCP {server_name}: {e}")
            return False

    def get_dynamic_tools_schema(self, server_filter: str = None) -> List[Dict]:
        if not server_filter or server_filter.lower() in ("all", "*", "miku"):
            return self.tools_schema_extension
        if server_filter.lower() in ("none", "ninguno", ""):
            return []
        prefix = f"mcp_{server_filter.lower()}_"
        return [t for t in self.tools_schema_extension if t.get("function", {}).get("name", "").lower().startswith(prefix)]

    async def execute_tool(self, namespaced_tool_name: str, kwargs: dict) -> str:
        if namespaced_tool_name not in self.tool_routing_map:
            return f"Error: La herramienta {namespaced_tool_name} no existe en la red MCP."
            
        server_name, original_tool_name = self.tool_routing_map[namespaced_tool_name]
        session = self.sessions.get(server_name)
        
        if not session:
            return f"Error: La sesión con el servidor {server_name} se perdió o está inicializando."
            
        try:
            result = await session.call_tool(original_tool_name, arguments=kwargs)
            text_outputs = []
            for item in result.content:
                if item.type == "text":
                    text_outputs.append(item.text)
                elif item.type == "resource":
                    text_outputs.append(f"[Recurso recibido: {getattr(item.resource, 'uri', 'unknown')}]")
            
            if not text_outputs:
                return "Ejecución exitosa, pero no se devolvió texto."
                
            return "\n".join(text_outputs)
            
        except Exception as e:
            return f"Error ejecutando herramienta MCP {original_tool_name}: {e}"

    async def close_all(self):
        for server_name, task in self.server_tasks.items():
            task.cancel()
        self.sessions.clear()

# Instancia global (singleton)
mcp_manager = MikuMCPManager()
