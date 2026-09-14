"""Source locations and results shared by validation and publication."""

from dataclasses import asdict, dataclass, field


@dataclass
class Diagnostic:
    rule_id: str
    severity: str
    path: str
    line: int
    message: str
    suggestion: str
    message_locale: str = "en"
    column: int = 1
    entity_id: str | None = None
    related_locations: list[dict] = field(default_factory=list)
    requested_locale: str = "en"
    locale_fallback: bool = False
    suggestion_locale: str = "en"
    parameters: dict[str, str] = field(default_factory=dict)


@dataclass
class Definition:
    id: str
    path: str
    line: int
    status: str
    title: str = ""

    @property
    def kind(self):
        return self.id.split("_", 1)[0]


@dataclass
class Reference:
    target: str
    path: str
    line: int
    relation: str = "links"
    source: str | None = None


@dataclass
class Document:
    path: str
    metadata: dict
    sections: dict[str, int] = field(default_factory=dict)
    section_titles: dict[str, str] = field(default_factory=dict)
    tasks: list[str] = field(default_factory=list)
    navigation: list[str] = field(default_factory=list)


@dataclass
class Result:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    definitions: dict[str, Definition] = field(default_factory=dict)
    references: list[Reference] = field(default_factory=list)
    documents: dict[str, Document] = field(default_factory=dict)
    deletion_checked: bool = False
    section_redirects: dict[str, str] = field(default_factory=dict)

    @property
    def valid(self):
        return not any(d.severity == "error" for d in self.diagnostics)

    def to_dict(self):
        return {"valid": self.valid, **asdict(self)}
