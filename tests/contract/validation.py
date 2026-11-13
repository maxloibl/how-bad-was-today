from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = yaml.safe_load((ROOT / "contracts/openapi.yaml").read_text(encoding="utf-8"))
RESOURCE = Resource.from_contents(CONTRACT, default_specification=DRAFT202012)
REGISTRY = Registry().with_resource("urn:daily-signal:contract", RESOURCE)


def assert_valid(instance: object, schema_name: str) -> None:
    schema = {"$ref": f"urn:daily-signal:contract#/components/schemas/{schema_name}"}
    errors = list(Draft202012Validator(schema, registry=REGISTRY).iter_errors(instance))
    assert not errors, [error.message for error in errors]
