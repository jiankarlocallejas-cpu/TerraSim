"""The reference solver must import without historical API/database extras."""
import os
import subprocess
import sys


def test_reference_service_import_does_not_load_legacy_database_stack():
    environment = os.environ.copy()
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import backend.services.paper_model; "
            "assert 'sqlalchemy' not in sys.modules; "
            "assert 'backend.services.user_service' not in sys.modules",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stderr

