from tradingview_mcp.server import mcp


def test_strategy_regime_score_tool_is_registered_with_annotations():
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}

    tool = tools["strategy_regime_score"]
    assert tool.annotations.title == "Strategy Regime Score"
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.destructiveHint is False


def test_oi_expected_range_score_tool_is_registered_with_annotations():
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}

    tool = tools["oi_expected_range_score"]
    assert tool.annotations.title == "OI Expected Range Score"
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.destructiveHint is False


def test_latest_trade_signal_tool_is_registered_with_annotations():
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}

    tool = tools["latest_trade_signal"]
    assert tool.annotations.title == "Latest Compact Trade Signal"
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.destructiveHint is False


def test_analyze_and_store_signal_tool_is_registered_with_annotations():
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}

    tool = tools["analyze_and_store_signal"]
    assert tool.annotations.title == "Analyze and Store Trade Signal"
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.destructiveHint is False


def test_store_ai_signal_response_tool_is_registered_with_annotations():
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}

    tool = tools["store_ai_signal_response"]
    assert tool.annotations.title == "Store AI Signal Response"
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.destructiveHint is False
