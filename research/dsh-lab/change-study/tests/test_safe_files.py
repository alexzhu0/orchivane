import os
import tempfile
import unittest
from pathlib import Path
from safe_files import read_task_file


class SafeFileTests(unittest.TestCase):
    def test_only_bounded_regular_files_are_read(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);plain=root/'plain';plain.write_bytes(b'abc')
            (root/'link').symlink_to(plain);os.mkfifo(root/'pipe')
            self.assertEqual(read_task_file(plain),b'abc')
            self.assertIsNone(read_task_file(plain,2))
            for path in (root/'link',root/'pipe',root,root/'missing'):
                self.assertIsNone(read_task_file(path))
