"""
Root Streamlit Entry Point.
Delegates to frontend/app.py so running either:
    streamlit run app.py
or
    streamlit run frontend/app.py
works seamlessly.
"""

import os
import sys
import runpy

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

frontend_target = os.path.join(PROJECT_ROOT, "frontend", "app.py")
runpy.run_path(frontend_target, run_name="__main__")
