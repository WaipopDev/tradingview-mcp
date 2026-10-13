"""Minimal MCP client for the MT5 terminal's built-in tester tools.

Reads the local terminal MCP API key from the terminal's own assistant.ini and
never prints or stores it. Only used to drive the simulated Strategy Tester.
"""
import asyncio
import json
import pathlib
import re
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

CONFIG = pathlib.Path(
    'C:/Users/waipo/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/config/assistant.ini')


def credentials() -> tuple[str, str]:
    text = CONFIG.read_bytes().decode('utf-16')
    section, endpoint, key = None, None, None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('['):
            section = line
        elif section == '[MCP.MetaTrader]' and '=' in line:
            name, value = line.split('=', 1)
            if name.strip() == 'Endpoint':
                endpoint = value.strip()
            elif name.strip() == 'ApiKey':
                key = value.strip()
    if not endpoint or not key:
        raise SystemExit('terminal MCP endpoint/key not configured; enable it in the terminal MCP settings')
    url = endpoint if endpoint.endswith('/mcp') else endpoint.rstrip('/') + '/mcp'
    return url, key


def redact(text: str, key: str) -> str:
    return text.replace(key, '<redacted>')


async def call(command: str, name: str | None, arguments: dict, timeout: float) -> str:
    url, key = credentials()
    headers = {'Authorization': f'Bearer {key}'}
    async with streamablehttp_client(url, headers=headers, sse_read_timeout=timeout) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if command == 'list':
                tools = await session.list_tools()
                return json.dumps(sorted(tool.name for tool in tools.tools))
            if command == 'schema':
                tools = await session.list_tools()
                for tool in tools.tools:
                    if tool.name == name:
                        return json.dumps({'name': tool.name, 'description': tool.description,
                                           'input': tool.inputSchema}, indent=2)
                return f'unknown tool {name}'
            result = await session.call_tool(name, arguments, read_timeout_seconds=None)
            parts = []
            for block in result.content:
                text = getattr(block, 'text', None)
                parts.append(text if text is not None else str(block))
            return redact(json.dumps({'isError': bool(result.isError), 'content': parts}, indent=2), key)


def main():
    command = sys.argv[1]
    if command == 'list':
        name, payload = None, {}
    elif command == 'schema':
        name, payload = sys.argv[2], {}
    else:
        name, payload = sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    print(asyncio.run(call(command, name, payload, 300)))


if __name__ == '__main__':
    main()
