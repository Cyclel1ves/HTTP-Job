import json
import time
import threading
import http.client
import unittest

import server


class APITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = "127.0.0.1"
        cls.port = 18080

        cls.thread = threading.Thread(
            target=server.run, args=(cls.host, cls.port), daemon=True
        )
        cls.thread.start()
        time.sleep(0.3)

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection(self.host, self.port, timeout=3)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            resp = conn.getresponse()
            data = resp.read()
            return resp.status, data
        finally:
            conn.close()

    def test_create_and_list_and_complete(self):
        payload = json.dumps({"title": "Gym", "priority": "low"}).encode("utf-8")
        status, data = self.request(
            "POST",
            "/tasks",
            body=payload,
            headers={"Content-Type": "application/json", "Content-Length": str(len(payload))},
        )
        self.assertEqual(status, 200)
        task = json.loads(data.decode("utf-8"))
        self.assertEqual(task["title"], "Gym")
        self.assertEqual(task["priority"], "low")
        self.assertEqual(task["isDone"], False)
        self.assertTrue(isinstance(task["id"], int))
        task_id = task["id"]

        status, data = self.request("GET", "/tasks")
        self.assertEqual(status, 200)
        arr = json.loads(data.decode("utf-8"))
        self.assertTrue(any(t["id"] == task_id for t in arr))

        status, data = self.request("POST", f"/tasks/{task_id}/complete")
        self.assertEqual(status, 200)
        self.assertEqual(data, b"")

        status, data = self.request("GET", "/tasks")
        arr = json.loads(data.decode("utf-8"))
        t = [x for x in arr if x["id"] == task_id][0]
        self.assertEqual(t["isDone"], True)

    def test_complete_nonexistent(self):
        status, data = self.request("POST", "/tasks/999999/complete")
        self.assertEqual(status, 404)
        self.assertEqual(data, b"")


if __name__ == "__main__":
    unittest.main()
