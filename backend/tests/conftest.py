import os
import tempfile

_TMP_DB = tempfile.mkdtemp(prefix="creatorai_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}/test.db"
os.environ["SIMULATED_RENDER"] = "true"
