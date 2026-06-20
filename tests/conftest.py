import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["CARBONCOACH_DB_PATH"] = os.path.join(
    tempfile.gettempdir(), "cc_test.db"
)
