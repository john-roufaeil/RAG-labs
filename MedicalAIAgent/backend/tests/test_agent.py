from app.tools import should_use_search_tool
from app.memory import ConversationMemory

def test_tool_routing():
    assert should_use_search_tool("Find nearby hospital in Cairo")
    assert not should_use_search_tool("Summarize these symptoms only")

def test_memory_trimming():
    mem = ConversationMemory(max_chars=200)
    sid = "s1"
    for i in range(10):
        mem.add_message(sid, "user", "headache " * 20 + str(i))
    assert len(mem.get_summary(sid)) > 0
