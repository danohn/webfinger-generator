from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from webfinger_generator import JRD, JRDValidationError, Link, generate_jrd


def test_link_href_and_template_are_mutually_exclusive() -> None:
    with pytest.raises(JRDValidationError):
        Link(rel="self", href="https://example.com", template="https://example.com/{uri}")


def test_jrd_requires_content() -> None:
    with pytest.raises(JRDValidationError):
        JRD()


def test_jrd_to_dict_round_trip() -> None:
    link = Link(
        rel="self",
        href="https://example.com/alice",
        type="application/activity+json",
        titles={"en": "Alice"},
        properties={"https://example.com/schema/name": "Alice"},
    )
    expires = datetime(2024, 1, 1, 12, 30, tzinfo=timezone.utc)

    descriptor = JRD(
        subject="acct:alice@example.com",
        aliases=["https://example.com/alice"],
        properties={"https://example.com/schema/pronouns": "she/her"},
        links=[link],
        expires=expires,
        additional_members={"subject_type": "https://schema.org/Person"},
    )

    payload = descriptor.to_dict()

    assert payload["subject"] == "acct:alice@example.com"
    assert payload["aliases"] == ["https://example.com/alice"]
    assert payload["properties"]["https://example.com/schema/pronouns"] == "she/her"
    assert payload["links"][0]["href"] == "https://example.com/alice"
    assert payload["links"][0]["titles"] == {"en": "Alice"}
    assert payload["expires"] == "2024-01-01T12:30:00Z"
    assert payload["subject_type"] == "https://schema.org/Person"


def test_generate_jrd_accepts_mappings_for_links() -> None:
    document = generate_jrd(
        "acct:bob@example.com",
        links=[{"rel": "self", "href": "https://example.com/bob"}],
        aliases=("https://example.com/bob",),
    )

    payload = json.loads(document)

    assert payload["subject"] == "acct:bob@example.com"
    assert payload["aliases"] == ["https://example.com/bob"]
    assert payload["links"] == [{"rel": "self", "href": "https://example.com/bob"}]


def test_alias_validation_rejects_empty_strings() -> None:
    with pytest.raises(JRDValidationError):
        JRD(subject="acct:carol@example.com", aliases=[""])
