from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from webfinger_generator import JRD, JRDValidationError, Link, generate_jrd


def test_link_href_and_template_are_mutually_exclusive() -> None:
    with pytest.raises(JRDValidationError):
        Link(rel="self", href="https://example.com", template="https://example.com/{uri}")


def test_jrd_requires_subject() -> None:
    with pytest.raises(JRDValidationError):
        JRD(subject="")


def test_subject_must_be_uri() -> None:
    with pytest.raises(JRDValidationError):
        JRD(subject="not-a-uri")


def test_aliases_must_be_uris() -> None:
    with pytest.raises(JRDValidationError):
        JRD(subject="acct:carol@example.com", aliases=["not-a-uri"])


def test_property_keys_must_be_uris() -> None:
    with pytest.raises(JRDValidationError):
        JRD(subject="acct:carol@example.com", properties={"name": "Alice"})


def test_property_values_may_be_null() -> None:
    descriptor = JRD(
        subject="acct:alice@example.com",
        properties={"https://example.com/schema/pronouns": None},
    )

    assert descriptor.to_dict()["properties"]["https://example.com/schema/pronouns"] is None


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


def test_link_property_values_may_be_null() -> None:
    link = Link(
        rel="self",
        href="https://example.com/alice",
        properties={"https://example.com/schema/pronouns": None},
    )

    assert link.to_dict()["properties"]["https://example.com/schema/pronouns"] is None


def test_alias_validation_rejects_empty_strings() -> None:
    with pytest.raises(JRDValidationError):
        JRD(subject="acct:carol@example.com", aliases=[""])


def test_link_requires_href_or_template() -> None:
    with pytest.raises(JRDValidationError):
        Link(rel="self")


def test_link_href_must_be_uri() -> None:
    with pytest.raises(JRDValidationError):
        Link(rel="self", href="not a uri")


def test_link_rel_must_be_registered_type_or_uri() -> None:
    with pytest.raises(JRDValidationError):
        Link(rel="invalid relation", href="https://example.com")


def test_link_rel_accepts_uri_relation_type() -> None:
    link = Link(rel="https://example.com/rel", href="https://example.com")

    assert link.rel == "https://example.com/rel"


def test_link_type_must_be_media_type() -> None:
    with pytest.raises(JRDValidationError):
        Link(rel="self", href="https://example.com", type="invalid")


def test_link_titles_keys_must_be_language_tags() -> None:
    with pytest.raises(JRDValidationError):
        Link(
            rel="self",
            href="https://example.com",
            titles={"123": "Invalid"},
        )


def test_link_titles_accept_und_language_tag() -> None:
    link = Link(
        rel="self",
        href="https://example.com",
        titles={"und": "Fallback"},
    )

    assert link.titles == {"und": "Fallback"}


def test_hreflang_values_must_be_language_tags() -> None:
    with pytest.raises(JRDValidationError):
        Link(
            rel="self",
            href="https://example.com",
            hreflang=["not a tag"],
        )


def test_hreflang_accepts_language_tags() -> None:
    link = Link(
        rel="self",
        href="https://example.com",
        hreflang=["en", "fr-CA"],
    )

    assert link.hreflang == ("en", "fr-CA")


def test_expires_string_must_be_rfc3339() -> None:
    with pytest.raises(JRDValidationError):
        JRD(subject="acct:dan@example.com", expires="2024-01-01T12:30:00")


def test_minimal_jrd_serialises_subject_only() -> None:
    descriptor = JRD(subject="acct:erin@example.com")

    assert descriptor.to_dict() == {"subject": "acct:erin@example.com"}
