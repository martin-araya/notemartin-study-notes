#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic HTML fixtures for F29 eval.

Builds docs-site/ with 5 HTML files:
  - index.html (main page with <nav> and canonical link)
  - intro.html (1st section)
  - install.html (2nd section, with canonical URL)
  - config.html (3rd section)
  - api.html (4th section)

Writes to evals/web-docs-sample/docs-site/.
"""

from __future__ import annotations

import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "docs-site"
BASE_URL = "https://example.com/docs/"


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="product" content="ExampleProduct">
  <meta name="version" content="1.2.3">
  <title>ExampleProduct Documentation</title>
  <link rel="canonical" href="https://example.com/docs/index.html">
</head>
<body>
  <nav>
    <a href="intro.html">Introduction</a>
    <a href="install.html">Installation</a>
    <a href="config.html">Configuration</a>
    <a href="api.html">API Reference</a>
  </nav>
  <header class="navbar">Skip to content</header>
  <div class="banner">Accept cookies</div>
  <main>
    <h1 id="welcome">Welcome to ExampleProduct</h1>
    <p>This is the main documentation page. Choose a section from the navigation.</p>
  </main>
  <footer>All rights reserved (c) 2026</footer>
</body>
</html>
"""


INTRO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Introduction - ExampleProduct</title>
  <link rel="canonical" href="https://example.com/docs/intro.html">
</head>
<body>
  <nav>
    <a href="intro.html">Introduction</a>
    <a href="install.html">Installation</a>
    <a href="config.html">Configuration</a>
    <a href="api.html">API Reference</a>
  </nav>
  <main>
    <h1 id="intro">Introduction</h1>
    <p>This section introduces ExampleProduct and its core concepts.</p>
    <h2 id="what-is">What is ExampleProduct?</h2>
    <p>ExampleProduct is a tool that does X.</p>
  </main>
</body>
</html>
"""


INSTALL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Installation - ExampleProduct</title>
  <link rel="canonical" href="https://example.com/docs/install.html">
</head>
<body>
  <nav>
    <a href="intro.html">Introduction</a>
    <a href="install.html">Installation</a>
    <a href="config.html">Configuration</a>
    <a href="api.html">API Reference</a>
  </nav>
  <main>
    <h1 id="install">Installation</h1>
    <p>Install ExampleProduct using the standard installer.</p>
    <h2 id="reqs">Requirements</h2>
    <p>You need Python 3.10+ and pip.</p>
    <h2 id="install-steps">Steps</h2>
    <p>Run pip install example-product to get started.</p>
  </main>
</body>
</html>
"""


CONFIG_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Configuration - ExampleProduct</title>
  <link rel="canonical" href="https://example.com/docs/config.html">
</head>
<body>
  <nav>
    <a href="intro.html">Introduction</a>
    <a href="install.html">Installation</a>
    <a href="config.html">Configuration</a>
    <a href="api.html">API Reference</a>
  </nav>
  <main>
    <h1 id="config">Configuration</h1>
    <p>Configure ExampleProduct via the config file at /etc/example-product.conf.</p>
    <h2 id="env-vars">Environment Variables</h2>
    <p>Set EXAMPLE_PRODUCT_HOME to the install directory.</p>
  </main>
</body>
</html>
"""


API_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>API Reference - ExampleProduct</title>
  <link rel="canonical" href="https://example.com/docs/api.html">
</head>
<body>
  <nav>
    <a href="intro.html">Introduction</a>
    <a href="install.html">Installation</a>
    <a href="config.html">Configuration</a>
    <a href="api.html">API Reference</a>
  </nav>
  <main>
    <h1 id="api">API Reference</h1>
    <p>The ExampleProduct API is organized in modules.</p>
    <h2 id="module-a">Module A</h2>
    <p>Functions for doing X.</p>
    <h2 id="module-b">Module B</h2>
    <p>Functions for doing Y.</p>
  </main>
</body>
</html>
"""


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    files = {
        "index.html": INDEX_HTML,
        "intro.html": INTRO_HTML,
        "install.html": INSTALL_HTML,
        "config.html": CONFIG_HTML,
        "api.html": API_HTML,
    }
    for name, content in files.items():
        path = FIXTURES / name
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path} ({len(content)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
