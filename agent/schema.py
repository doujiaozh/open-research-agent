from pydantic import BaseModel, Field
from typing import Any, Literal

class Decision(BaseModel):
    thought: str = Field(description="简短推理")
    action: Literal[
        "web_search", "fetch_url", "read_file", "write_file", "final"
    ] = Field(description="下一步动作")
    args: dict[str, Any] = Field(default_factory=dict)
    done: bool = False
    final_answer: str | None = None

class Step(BaseModel):
    step: int
    action: str
    args: dict[str, Any]
    observation: str

class AgentState(BaseModel):
    goal: str
    plan: list[str] = []
    history: list[Step] = []
    short_memory: list[str] = []
    artifacts: dict[str, str] = {}
    permissions: dict[str, bool] = {
        "read": True,
        "write": False,
        "send": False,
        "pay": False,
    }