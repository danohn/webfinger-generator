# webfinger-generator

`webfinger-generator` offers lightweight utilities for composing
[WebFinger](https://datatracker.ietf.org/doc/html/rfc7033) JSON Resource
Descriptors (JRDs). It exposes a small, typed API that makes it easy to build
valid responses that can be serialised directly into JSON payloads.

## Installation

The project targets Python 3.12 and above. Install it from PyPI with your
preferred package manager:

```bash
pip install webfinger-generator
```

If you prefer [uv](https://github.com/astral-sh/uv) you can add it to an
environment with:

```bash
uv add webfinger-generator
```

## Features

- `JRD` and `Link` dataclasses with validation rules derived from RFC&nbsp;7033.
- Helpers for serialising descriptors to dictionaries or JSON strings.
- Support for advanced members such as `expires`, language-specific titles,
  additional properties, and arbitrary extension members.

## Usage

### Building descriptors with dataclasses

```python
from datetime import datetime, timezone
from webfinger_generator import JRD, Link

link = Link(
    rel="self",
    href="https://example.com/alice",
    type="text/html",
    titles={"en": "Alice"},
)

descriptor = JRD(
    subject="acct:alice@example.com",
    aliases=["https://example.com/alice"],
    properties={"https://schema.org/name": "Alice"},
    links=[link],
    expires=datetime(2024, 1, 1, tzinfo=timezone.utc),
    additional_members={"subject_type": "https://schema.org/Person"},
)

payload = descriptor.to_dict()
```

The returned dictionary is ready for JSON serialisation and only contains
members that were provided. Any invalid inputs raise `JRDValidationError` with a
descriptive message so you can provide useful feedback to callers.

### Serialising to JSON

```python
from webfinger_generator import generate_jrd

body = generate_jrd(
    "acct:alice@example.com",
    aliases=["https://example.com/alice"],
    links=[{"rel": "self", "href": "https://example.com/alice"}],
    indent=2,
)
```

The `generate_jrd` convenience wrapper accepts either `Link` instances or
plain mapping definitions, performs the same validations as `JRD`, and returns
a JSON string in one step.

### Working with optional members

The dataclasses expose optional fields for less common JRD elements:

- Provide `template` instead of `href` to use URI templates.
- Supply `titles`, `properties`, or `hreflang` mappings on `Link` objects for
  language-specific metadata.
- Use `additional_members` on `JRD` to attach custom extension members without
  manual dictionary manipulation.

## Development

This repository uses `uv` for dependency management. To set up a virtual
environment and run the tests locally:

```bash
uv sync
uv run pytest
```

To experiment in a Python REPL with the project dependencies resolved:

```bash
uv run python
```

## License

webfinger-generator is released under the terms of the GNU General Public
License v3.0. See [LICENSE](LICENSE) for details.
