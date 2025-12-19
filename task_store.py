from __future__ import annotations

import json
import os
import tempfile
from threading import Lock
from typing import List, Optional

from models import Task, ALLOWED_PRIORITIES


class TaskStore:

    def __init__(self, filepath: str = "tasks.txt") -> None:
        self._filepath = filepath
        self._lock = Lock()
        self._tasks: List[Task] = []
        self._next_id: int = 1
        self.load()

    def load(self) -> None:
        with self._lock:
            if not os.path.exists(self._filepath):
                self._tasks = []
                self._next_id = 1
                return

            try:
                with open(self._filepath, "r", encoding="utf-8") as f:
                    raw = f.read().strip()
                    if not raw:
                        self._tasks = []
                        self._next_id = 1
                        return

                    data = json.loads(raw)
                    if not isinstance(data, list):
                        raise ValueError("tasks file must contain a JSON list")

                    tasks: List[Task] = []
                    max_id = 0
                    for item in data:
                        if not isinstance(item, dict):
                            continue
                        t = Task.from_dict(item)
                        tasks.append(t)
                        if t.task_id > max_id:
                            max_id = t.task_id

                    self._tasks = tasks
                    self._next_id = max_id + 1 if max_id > 0 else 1
            except Exception:
                self._tasks = []
                self._next_id = 1

    def save(self) -> None:
        with self._lock:
            payload = [t.to_dict() for t in self._tasks]

            dir_name = os.path.dirname(os.path.abspath(self._filepath)) or "."
            fd, tmp_path = tempfile.mkstemp(prefix="tasks_", suffix=".tmp", dir=dir_name)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                    json.dump(payload, tmp, ensure_ascii=False)
                os.replace(tmp_path, self._filepath)
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

    def list_tasks(self) -> List[Task]:
        with self._lock:
            return list(self._tasks)

    def create_task(self, title: str, priority: str) -> Task:
        title = (title or "").strip()
        priority = (priority or "").strip()

        if not title:
            raise ValueError("title is required")
        if priority not in ALLOWED_PRIORITIES:
            raise ValueError("priority must be one of: low, normal, high")

        with self._lock:
            task = Task(title=title, priority=priority, is_done=False, task_id=self._next_id)
            self._next_id += 1
            self._tasks.append(task)

        self.save()
        return task

    def complete_task(self, task_id: int) -> bool:
        with self._lock:
            for t in self._tasks:
                if t.task_id == task_id:
                    if not t.is_done:
                        t.is_done = True
                    break
            else:
                return False

        self.save()
        return True

    def get_task(self, task_id: int) -> Optional[Task]:
        with self._lock:
            for t in self._tasks:
                if t.task_id == task_id:
                    return t
        return None
