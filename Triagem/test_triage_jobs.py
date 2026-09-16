import os
import tempfile
import time
import unittest
from pathlib import Path

from triage_jobs import cleanup_old_jobs, create_job, queue_position, read_status, write_json_atomic


class TriageJobsTests(unittest.TestCase):
    def test_jobs_receive_isolated_directories_and_queue_positions(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            first = create_job(base, {"reaction": "reforma", "metals": ["Ni"]})
            time.sleep(0.01)
            second = create_job(base, {"reaction": "rwgs", "metals": ["Fe"]})
            self.assertNotEqual(first, second)
            self.assertEqual(queue_position(first, base), 1)
            self.assertEqual(queue_position(second, base), 2)
            self.assertEqual(read_status(first)["state"], "queued")

    def test_cleanup_removes_only_old_finalized_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            completed = create_job(base, {"reaction": "reforma", "metals": ["Ni"]})
            active = create_job(base, {"reaction": "rwgs", "metals": ["Fe"]})
            write_json_atomic(completed / "status.json", {"state": "completed"})
            old = time.time() - 26 * 3600
            for path in completed.rglob("*"):
                os.utime(path, (old, old))
            os.utime(completed, (old, old))
            removed = cleanup_old_jobs(base, max_age_hours=24)
            self.assertEqual(removed, 1)
            self.assertFalse(completed.exists())
            self.assertTrue(active.exists())

    def test_protected_job_is_never_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            job = create_job(base, {"reaction": "reforma", "metals": ["Ni"]})
            write_json_atomic(job / "status.json", {"state": "failed"})
            old = time.time() - 26 * 3600
            for path in job.rglob("*"):
                os.utime(path, (old, old))
            self.assertEqual(cleanup_old_jobs(base, protected={job}), 0)
            self.assertTrue(job.exists())


if __name__ == "__main__":
    unittest.main()
