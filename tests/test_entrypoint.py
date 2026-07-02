import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_main_exports_wsgi_app():
    main = importlib.import_module("main")
    assert callable(getattr(main, "app", None))
