from types import SimpleNamespace

from app.agents.master_agent import extract_tools_used


def test_extract_tools_used_preserves_unique_tool_order() -> None:
    run_result = SimpleNamespace(
        new_items=[
            SimpleNamespace(type="message_output_item"),
            SimpleNamespace(type="tool_call_item", tool_name="rag_specialist"),
            SimpleNamespace(type="tool_call_item", tool_name="rag_specialist"),
            SimpleNamespace(type="tool_call_item", tool_name="finance_specialist"),
        ]
    )

    assert extract_tools_used(run_result) == [
        "rag_specialist",
        "finance_specialist",
    ]
