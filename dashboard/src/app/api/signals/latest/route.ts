import { execFile } from "node:child_process";
import { homedir } from "node:os";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const symbol = url.searchParams.get("symbol") ?? "XAUUSD";
  const timeframe = url.searchParams.get("timeframe") ?? "15m";
  const repoRoot = path.resolve(process.cwd(), "..");
  const dbPath = process.env.TRADINGVIEW_MCP_DB_PATH ?? path.join(homedir(), ".tradingview-mcp", "trading_signals.sqlite3");
  const code = `
import json
from tradingview_mcp.server import latest_trade_signal
print(json.dumps(latest_trade_signal(${JSON.stringify(symbol)}, ${JSON.stringify(timeframe)}), ensure_ascii=False))
`;

  try {
    const { stdout } = await execFileAsync("uv", ["run", "python", "-c", code], {
      cwd: repoRoot,
      env: { ...process.env, TRADINGVIEW_MCP_DB_PATH: dbPath },
      timeout: 15000,
      maxBuffer: 1024 * 1024,
    });
    const jsonLine = stdout.trim().split(/\r?\n/).at(-1);
    if (!jsonLine) {
      return Response.json({ error: { code: "EMPTY_PYTHON_OUTPUT", retryable: true } }, { status: 502 });
    }
    return Response.json(JSON.parse(jsonLine));
  } catch (error) {
    return Response.json(
      {
        error: {
          code: "SIGNAL_READ_FAILED",
          message: error instanceof Error ? error.message : String(error),
          retryable: true,
        },
      },
      { status: 500 },
    );
  }
}
