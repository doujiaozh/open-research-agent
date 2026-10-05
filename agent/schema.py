from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field





class Decision(BaseModel):

    thought: str = Field(default="", description="简短推理")

    action: Literal["web_search", "fetch_url", "read_file", "write_file", "final"] = Field(description="下一步动作")

    args: Dict[str, Any] = Field(default_factory=dict)

    done: bool = False

    final_answer: Optional[str] = None





class Step(BaseModel):

    step: int

    action: str

    args: Dict[str, Any]

    observation: str





class AgentState(BaseModel):

    goal: str

    plan: List[str] = []

    history: List[Step] = []

    short_memory: List[str] = []

    artifacts: Dict[str, str] = {}

    permissions: Dict[str, bool] = {

        "read": True,

        "write": False,

        "send": False,

        "pay": False,

    }

