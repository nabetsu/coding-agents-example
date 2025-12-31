from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import main


def test_build_model_uses_env_key(monkeypatch):
    captured = {}

    class FakeProvider:
        def __init__(self, api_key):
            captured["api_key"] = api_key

    class FakeModel:
        def __init__(self, name, provider):
            captured["name"] = name
            captured["provider"] = provider

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(main, "OpenAIProvider", FakeProvider)
    monkeypatch.setattr(main, "OpenAIChatModel", FakeModel)

    model = main.build_model()

    assert isinstance(model, FakeModel)
    assert captured["api_key"] == "test-key"
    assert captured["name"] == "gpt-4o"
    assert isinstance(captured["provider"], FakeProvider)


def test_build_toolsets_wires_server_config(monkeypatch):
    calls = []

    class FakeServer:
        def __init__(self, command, args, env, tool_prefix=None):
            calls.append(
                {
                    "command": command,
                    "args": args,
                    "env": env,
                    "tool_prefix": tool_prefix,
                }
            )

    monkeypatch.setattr(main, "MCPServerStdio", FakeServer)
    monkeypatch.setattr(main, "_make_code_reasoning_patch", lambda: "/tmp/patch.cjs")
    monkeypatch.setattr(main.os, "getcwd", lambda: "/repo")
    monkeypatch.setenv("NODE_OPTIONS", "--trace-warnings")

    toolsets = main.build_toolsets()

    assert len(toolsets) == 2
    assert calls[0]["command"] == "npx"
    assert calls[0]["args"] == [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/repo",
    ]
    assert calls[0]["env"]["LOG_LEVEL"] == "error"

    assert calls[1]["command"] == "npx"
    assert calls[1]["args"] == ["-y", "@mettamatt/code-reasoning@latest"]
    assert calls[1]["tool_prefix"] == "code_reasoning"
    assert calls[1]["env"]["LOG_LEVEL"] == "error"
    assert calls[1]["env"]["MCP_DEBUG"] == "false"
    assert "--require /tmp/patch.cjs" in calls[1]["env"]["NODE_OPTIONS"]


def test_build_agent_uses_defaults(monkeypatch):
    captured = {}

    def fake_build_model():
        return "model"

    def fake_build_toolsets():
        return ["toolset"]

    class FakeAgent:
        def __init__(self, instructions, model, toolsets):
            captured["instructions"] = instructions
            captured["model"] = model
            captured["toolsets"] = toolsets

    monkeypatch.setattr(main, "build_model", fake_build_model)
    monkeypatch.setattr(main, "build_toolsets", fake_build_toolsets)
    monkeypatch.setattr(main, "Agent", FakeAgent)

    agent = main.build_agent()

    assert isinstance(agent, FakeAgent)
    assert captured["instructions"] == main.instructions
    assert captured["model"] == "model"
    assert captured["toolsets"] == ["toolset"]
