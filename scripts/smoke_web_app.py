"""Prove the interface renders, not merely that a port answers.

Streamlit serves `/_stcore/health` from the server process, which starts
before and independently of the application script. A health probe therefore
returns 200 for an application that cannot import, and the script only runs
once a client connects, so its traceback never reaches the server log either.
A reviewer running the reproduction would see a green check on a broken app.

`AppTest` executes the script the way a session does and surfaces whatever it
raised, so a failure here means the interface is actually broken.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

# AppTest runs the script without a browser session, so Streamlit logs a
# "missing ScriptRunContext" warning it documents as safe to ignore in bare
# mode. Silencing that one logger keeps the reproduction output free of a
# warning a reviewer cannot act on. Errors are unaffected: anything the script
# raises still arrives through `AppTest.exception` below.
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web" / "app.py"

# The application imports `web` and `src` as packages, which resolve from the
# repository root rather than from this script's directory.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPT_TIMEOUT_SECONDS = 120

# Streamlit only executes the page the navigation radio selects, so loading the
# application once exercises exactly one of these. A reviewer can open every
# one, so every one has to render.
NAVIGATION_KEY = "page"

# Rendering "something" is not enough: an anchor per page catches a silently
# empty render, which raises nothing.
REQUIRED_HEADING_BY_PAGE = {
    "Overview": "Reproducible corpus overview",
}


def _rendered_text(app: AppTest) -> str:
    parts = [element.value for element in app.title] + [element.value for element in app.header]
    parts += [element.value for element in app.subheader]
    parts += [str(element.value) for element in app.markdown]
    return "\n".join(str(part) for part in parts)


def _fail_on_exception(app: AppTest, page: str) -> None:
    if app.exception:
        raised = "\n".join(str(item.value) for item in app.exception)
        raise SystemExit(f"the {page} page raised while rendering:\n{raised}")


def main() -> int:
    if not APP.exists():
        raise SystemExit(f"application not found at {APP}")

    app = AppTest.from_file(str(APP), default_timeout=SCRIPT_TIMEOUT_SECONDS)
    app.run()
    _fail_on_exception(app, "opening")

    navigation = app.radio(key=NAVIGATION_KEY)
    for page in navigation.options:
        app.radio(key=NAVIGATION_KEY).set_value(page).run()
        _fail_on_exception(app, page)

        anchor = REQUIRED_HEADING_BY_PAGE.get(page)
        rendered = _rendered_text(app)
        if anchor and anchor not in rendered:
            raise SystemExit(f"the {page} page rendered without {anchor!r}")
        if not rendered.strip():
            raise SystemExit(f"the {page} page rendered nothing")
        print(f"  {page}: rendered")

    print(f"Every page rendered without exceptions ({len(navigation.options)} pages).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
