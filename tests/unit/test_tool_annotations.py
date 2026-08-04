"""Every MCP tool must carry directory-grade annotations.

Both official marketplaces (Anthropic's Connectors Directory and OpenAI's
ChatGPT plugin directory) require each tool to declare a human-readable
`title` and the applicable safety hint. Submissions with unannotated tools
are rejected at the Tools step of the portal, so this test makes the
requirement permanent: a newly added tool without annotations fails CI here
before it can fail a directory review.

Most tools in this server are read-only market analysis. Tools that persist
local SQLite cache rows must explicitly set readOnlyHint=False so MCP clients do
not treat them as side-effect-free. None of these tools place trades, delete
data, or perform destructive external actions, so destructiveHint remains False
across the board.
"""
from tradingview_mcp.server import mcp


WRITE_TOOLS = {"analyze_and_store_signal", "store_ai_signal_response"}


def _all_tools():
    tools = mcp._tool_manager.list_tools()
    assert len(tools) >= 30, f"tool count suspiciously low: {len(tools)}"
    return tools


def test_every_tool_has_annotations_with_title():
    missing = [t.name for t in _all_tools() if t.annotations is None or not (t.annotations.title or "").strip()]
    assert not missing, f"tools missing annotations/title (directory submissions reject these): {missing}"


def test_read_only_hint_matches_side_effect_profile():
    tools = _all_tools()

    missing_write_tools = WRITE_TOOLS - {t.name for t in tools}
    assert missing_write_tools == set(), f"expected write tools not registered: {missing_write_tools}"

    wrong_read_only = [
        t.name
        for t in tools
        if t.name not in WRITE_TOOLS and (t.annotations is None or t.annotations.readOnlyHint is not True)
    ]
    wrong_write_tools = [
        t.name
        for t in tools
        if t.name in WRITE_TOOLS and (t.annotations is None or t.annotations.readOnlyHint is not False)
    ]

    assert wrong_read_only == [], f"read-only tools not declared read-only: {wrong_read_only}"
    assert wrong_write_tools == [], f"write tools not declared with readOnlyHint=False: {wrong_write_tools}"


def test_every_tool_explicitly_declares_non_destructive():
    # OpenAI's plugin scanner requires an EXPLICIT true/false for
    # destructiveHint on every tool — omitting it fails the MCP scan step.
    missing = [t.name for t in _all_tools() if t.annotations is None or t.annotations.destructiveHint is not False]
    assert missing == [], f"tools without explicit destructiveHint=False: {missing}"


def test_titles_are_unique_and_human_readable():
    tools = _all_tools()
    titles = [t.annotations.title for t in tools]
    assert len(set(titles)) == len(titles), "duplicate tool titles confuse directory listings"
    for title in titles:
        assert title != title.lower(), f"title looks like an identifier, not a human title: {title!r}"
        assert "_" not in title, f"title contains underscores: {title!r}"
