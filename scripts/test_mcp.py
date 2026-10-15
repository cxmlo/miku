import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
import sys

async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server_sqlite", "--db-path", "mikumemoria.db"]
    )
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Conectado a sqlite!")
                res = await session.list_tools()
                print(res)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
