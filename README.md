# webfinger-generator

Utilities for composing [WebFinger](https://datatracker.ietf.org/doc/html/rfc7033)
JSON Resource Descriptors (JRDs). The project focuses on providing a typed API
for programmatically building compliant responses that can be serialized directly
into JSON payloads.

## Features

- Lightweight `JRD` and `Link` dataclasses with validation rules derived from
  RFC&nbsp;7033.
- Convenience helpers for serialising descriptors to dictionaries or JSON
  strings.
- Support for advanced members such as `expires`, language specific titles,
  and additional custom members.

## Quick start

The project uses [uv](https://github.com/astral-sh/uv) for dependency
management. Create a virtual environment and run the unit tests with:

```bash
uv sync
uv run pytest
```

To experiment in a REPL:

```bash
uv run python
```

## Usage

```python
from datetime import datetime, timezone
from webfinger_generator import JRD, Link, generate_jrd

link = Link(rel="self", href="https://example.com/alice", type="text/html")
descriptor = JRD(
    subject="acct:alice@example.com",
    aliases=["https://example.com/alice"],
    properties={"https://schema.org/name": "Alice"},
    links=[link],
    expires=datetime(2024, 1, 1, tzinfo=timezone.utc),
)

# Obtain a dictionary
payload = descriptor.to_dict()

# Or a JSON string ready to be served
body = descriptor.to_json(indent=2)

# A helper is available when you only care about JSON output
body = generate_jrd(
    "acct:alice@example.com",
    aliases=["https://example.com/alice"],
    links=[{"rel": "self", "href": "https://example.com/alice"}],
    indent=2,
)
```

## License

webfinger-generator is released under the terms of the GNU General Public
License v3.0. See [LICENSE](LICENSE) for details.
