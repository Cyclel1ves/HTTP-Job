from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


ALLOWED_PRIORITIES = {"low", "normal", "high"}


@dataclass
class Task:
    title: str
    priority: str
    is_done: bool
    task_id: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "priority": self.priority,
            "isDone": self.is_done,
            "id": self.task_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Task":
        return Task(
            title=str(data["title"]),
            priority=str(data["priority"]),
            is_done=bool(data["isDone"]),
            task_id=int(data["id"]),
        )
