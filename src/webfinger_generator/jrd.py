"""Data structures for generating RFC 7033 compliant JRD documents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

__all__ = [
    "JRD",
    "Link",
    "JRDValidationError",
    "generate_jrd",
]


class JRDValidationError(ValueError):
    """Raised when input data cannot be represented as a valid JRD."""


def _require_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise JRDValidationError(f"{field} must be a non-empty string.")

    if not value:
        raise JRDValidationError(f"{field} must be a non-empty string.")

    if value != value.strip():
        raise JRDValidationError(
            f"{field} must not contain leading or trailing whitespace."
        )

    return value


def _require_uri(value: Any, *, field: str) -> str:
    candidate = _require_string(value, field=field)
    parsed = urlparse(candidate)

    if not parsed.scheme:
        raise JRDValidationError(f"{field} must be an absolute URI with a scheme.")

    if not (parsed.netloc or parsed.path):
        raise JRDValidationError(f"{field} must contain a URI path or authority component.")

    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        raise JRDValidationError(f"{field} must include a network location component.")

    return candidate


def _validate_string_sequence(
    name: str,
    values: Sequence[str],
    *,
    require_uri: bool = False,
    require_language_tag: bool = False,
) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise JRDValidationError(f"{name} must be a sequence of strings.")

    cleaned: list[str] = []
    for idx, value in enumerate(values):
        if require_uri:
            candidate = _require_uri(value, field=f"{name}[{idx}]")
        else:
            candidate = _require_string(value, field=f"{name}[{idx}]")
        if require_language_tag:
            candidate = _require_language_tag(candidate, field=f"{name}[{idx}]")
        cleaned.append(candidate)
    return tuple(cleaned)


def _validate_string_mapping(
    name: str,
    mapping: Mapping[str, str | None],
    *,
    require_uri_keys: bool = False,
    allow_null_values: bool = False,
) -> dict[str, str | None]:
    if not isinstance(mapping, Mapping):
        raise JRDValidationError(f"{name} must be a mapping of string keys to string values.")

    cleaned: dict[str, str | None] = {}
    for key, value in mapping.items():
        if require_uri_keys:
            validated_key = _require_uri(key, field=f"{name} key")
        else:
            if not isinstance(key, str) or not key:
                raise JRDValidationError(
                    f"{name} keys must be non-empty strings (got {key!r})."
                )
            if key != key.strip():
                raise JRDValidationError(
                    f"{name} keys must not contain leading or trailing whitespace."
                )
            validated_key = key

        if value is None:
            if not allow_null_values:
                raise JRDValidationError(
                    f"{name} values must be strings (key {validated_key!r} had {value!r})."
                )
        else:
            if not isinstance(value, str):
                raise JRDValidationError(
                    f"{name} values must be strings (key {validated_key!r} had {value!r})."
                )
            if value != value.strip():
                raise JRDValidationError(
                    f"{name} values must not contain leading or trailing whitespace (key {validated_key!r})."
                )
        cleaned[validated_key] = value
    return cleaned


def _coerce_link(value: Mapping[str, Any] | "Link") -> "Link":
    if isinstance(value, Link):
        return value
    if not isinstance(value, Mapping):
        raise JRDValidationError("Links must be Link instances or mapping definitions.")
    return Link(**value)


def _format_rfc3339(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _validate_rfc3339_string(value: str, *, field: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise JRDValidationError(f"{field} must be an RFC 3339 formatted timestamp.") from exc

    if parsed.tzinfo is None:
        raise JRDValidationError(f"{field} must include a timezone offset.")


_REGISTERED_RELATION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]*$")


def _require_relation_type(value: Any, *, field: str) -> str:
    candidate = _require_string(value, field=field)

    if _REGISTERED_RELATION_RE.fullmatch(candidate):
        return candidate

    try:
        return _require_uri(candidate, field=field)
    except JRDValidationError as exc:
        raise JRDValidationError(
            f"{field} must be a registered relation type or an absolute URI."
        ) from exc


_MEDIA_TYPE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*$")


def _require_media_type(value: Any, *, field: str) -> str:
    candidate = _require_string(value, field=field)
    if not _MEDIA_TYPE_RE.fullmatch(candidate):
        raise JRDValidationError(f"{field} must be a valid media type string.")
    return candidate


_LANGUAGE_TAG_RE = re.compile(r"^[A-Za-z]{1,8}(?:-[A-Za-z0-9]{1,8})*$")


def _require_language_tag(value: Any, *, field: str) -> str:
    candidate = _require_string(value, field=field)
    if candidate.lower() == "und":
        return candidate
    if not _LANGUAGE_TAG_RE.fullmatch(candidate):
        raise JRDValidationError(
            f"{field} must be a valid BCP 47 language tag or 'und'."
        )
    return candidate


def _validate_titles_mapping(mapping: Mapping[str, str]) -> dict[str, str]:
    cleaned = _validate_string_mapping("titles", mapping)
    validated: dict[str, str] = {}
    for key, value in cleaned.items():
        if value is None:
            raise JRDValidationError("titles values must be strings.")
        validated[_require_language_tag(key, field="titles key")] = value
    return validated


@dataclass(slots=True)
class Link:
    """A single WebFinger link description."""

    rel: str
    href: str | None = None
    type: str | None = None
    titles: Mapping[str, str] | None = None
    properties: Mapping[str, str | None] | None = None
    template: str | None = None
    hreflang: Sequence[str] | None = None

    def __post_init__(self) -> None:
        self.rel = _require_relation_type(self.rel, field="rel")

        if self.href is not None:
            self.href = _require_uri(self.href, field="href")
        if self.template is not None:
            self.template = _require_uri(self.template, field="template")
        if self.href and self.template:
            raise JRDValidationError("A link cannot contain both 'href' and 'template'.")
        if self.href is None and self.template is None:
            raise JRDValidationError("A link must contain either 'href' or 'template'.")

        if self.type is not None:
            self.type = _require_media_type(self.type, field="type")
        if self.titles is not None:
            self.titles = _validate_titles_mapping(self.titles)
        if self.properties is not None:
            self.properties = _validate_string_mapping(
                "properties",
                self.properties,
                require_uri_keys=True,
                allow_null_values=True,
            )
        if self.hreflang is not None:
            self.hreflang = _validate_string_sequence(
                "hreflang", self.hreflang, require_language_tag=True
            )

    def to_dict(self) -> dict[str, Any]:
        """Return the link as a JSON-serialisable dictionary."""

        payload: dict[str, Any] = {"rel": self.rel}
        if self.type is not None:
            payload["type"] = self.type
        if self.href is not None:
            payload["href"] = self.href
        if self.template is not None:
            payload["template"] = self.template
        if self.titles:
            payload["titles"] = dict(self.titles)
        if self.properties:
            payload["properties"] = dict(self.properties)
        if self.hreflang:
            payload["hreflang"] = list(self.hreflang)
        return payload


@dataclass(slots=True)
class JRD:
    """Representation of a JSON Resource Descriptor."""

    subject: str
    aliases: Sequence[str] | None = None
    properties: Mapping[str, str | None] | None = None
    links: Sequence[Mapping[str, Any] | Link] | None = None
    expires: datetime | str | None = None
    additional_members: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        self.subject = _require_uri(self.subject, field="subject")

        if self.aliases is not None:
            self.aliases = _validate_string_sequence(
                "aliases", self.aliases, require_uri=True
            )

        if self.properties is not None:
            self.properties = _validate_string_mapping(
                "properties",
                self.properties,
                require_uri_keys=True,
                allow_null_values=True,
            )

        if self.links is not None:
            if not isinstance(self.links, Sequence) or isinstance(self.links, (str, bytes)):
                raise JRDValidationError("links must be a sequence of link definitions.")
            processed: list[Link] = []
            for item in self.links:
                processed.append(_coerce_link(item))
            self.links = tuple(processed)

        if self.expires is not None and not isinstance(self.expires, (datetime, str)):
            raise JRDValidationError("expires must be a datetime or RFC 3339 formatted string.")
        if isinstance(self.expires, str):
            if not self.expires:
                raise JRDValidationError("expires strings must be non-empty.")
            _validate_rfc3339_string(self.expires, field="expires")

        if self.additional_members is not None:
            if not isinstance(self.additional_members, Mapping):
                raise JRDValidationError("additional_members must be a mapping.")
            cleaned: dict[str, Any] = {}
            for key, value in self.additional_members.items():
                if not isinstance(key, str) or not key:
                    raise JRDValidationError(
                        f"additional_members keys must be non-empty strings (got {key!r})."
                    )
                if key != key.strip():
                    raise JRDValidationError(
                        f"additional_members keys must not contain leading or trailing whitespace."
                    )
                if key in {"subject", "aliases", "properties", "links", "expires"}:
                    raise JRDValidationError(
                        f"additional member '{key}' conflicts with a standard JRD member."
                    )
                cleaned[key] = value
            self.additional_members = cleaned

    def to_dict(self) -> dict[str, Any]:
        """Convert the descriptor into a dictionary."""

        payload: dict[str, Any] = {}
        if self.subject is not None:
            payload["subject"] = self.subject
        if self.aliases:
            payload["aliases"] = list(self.aliases)
        if self.properties:
            payload["properties"] = dict(self.properties)
        if self.links:
            payload["links"] = [link.to_dict() for link in self.links]
        if self.expires is not None:
            payload["expires"] = (
                _format_rfc3339(self.expires)
                if isinstance(self.expires, datetime)
                else self.expires
            )
        if self.additional_members:
            payload.update(self.additional_members)
        return payload

    def to_json(self, *, indent: int | None = None, ensure_ascii: bool = False) -> str:
        """Serialise the descriptor to a JSON string."""

        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii)


def generate_jrd(
    subject: str,
    *,
    aliases: Sequence[str] | None = None,
    properties: Mapping[str, str | None] | None = None,
    links: Sequence[Mapping[str, Any] | Link] | None = None,
    expires: datetime | str | None = None,
    additional_members: Mapping[str, Any] | None = None,
    indent: int | None = None,
    ensure_ascii: bool = False,
) -> str:
    """Convenience wrapper that returns a JSON document for the supplied data.

    Args:
        subject: Absolute URI identifying the WebFinger resource.
        aliases: Optional sequence of URI aliases.
        properties: Optional mapping of property URI keys to string or null values.
        links: Optional sequence of :class:`Link` instances or link mappings.
        expires: Optional datetime or RFC 3339 timestamp string.
        additional_members: Optional mapping of extension members.
        indent: Number of spaces to indent the generated JSON.
        ensure_ascii: Whether JSON output should escape non-ASCII characters.
    """

    descriptor = JRD(
        subject=subject,
        aliases=aliases,
        properties=properties,
        links=links,
        expires=expires,
        additional_members=additional_members,
    )
    return descriptor.to_json(indent=indent, ensure_ascii=ensure_ascii)
