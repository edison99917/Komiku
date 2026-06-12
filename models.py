from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str


@dataclass
class Chapter:
    number: float
    url: str
