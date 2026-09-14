"""Offline IDs with a local date and 80 uniformly random bits."""

from datetime import date
import secrets
from tao_messages import Message


def new_id(kind, registry, existing, *, today=None, random_bytes=secrets.token_bytes):
    if kind not in {"DOC", "REQ", "UC", "ADR", "TASK", "CHG", "EVD"}:
        raise ValueError(Message('Unknown ID type: {arg0}', kind))
    rule = registry["id"]
    prefix = kind + "_" + (today or date.today()).strftime("%Y%m%d") + "_"
    for _ in range(rule["maximum_generation_attempts"]):
        number = int.from_bytes(random_bytes(rule["random_bytes"]), "big")
        suffix = "".join(rule["alphabet"][(number >> shift) & 31] for shift in range(75, -1, -5))
        identity = prefix + suffix
        if identity not in existing:
            return identity
    raise ValueError("ID collision after three candidates; no ID allocated.")
