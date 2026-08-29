import sys
import os

# Ensure src is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from sdlc_immune.web.app import run_server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)
