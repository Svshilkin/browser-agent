from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any


@dataclass
class Input:
    """Form input field model"""
    name: str
    type: str  # text, password, email, checkbox, radio, etc.
    selector: str
    value: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Form:
    """HTML form model"""
    selector: str
    action: Optional[str] = None
    method: str = "POST"
    inputs: List[Input] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "selector": self.selector,
            "action": self.action,
            "method": self.method,
            "inputs": [inp.to_dict() for inp in self.inputs]
        }


@dataclass
class Button:
    """Button element model"""
    text: str
    selector: str
    type: str = "button"  # button, submit, reset
    form_selector: Optional[str] = None  # parent form if any
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Link:
    """Hyperlink model"""
    text: str
    href: str
    selector: str
    title: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PageStructure:
    """Complete page structure model"""
    title: str
    url: str
    buttons: List[Button] = field(default_factory=list)
    forms: List[Form] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    headings: List[str] = field(default_factory=list)
    paragraphs: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "buttons": [b.to_dict() for b in self.buttons],
            "forms": [f.to_dict() for f in self.forms],
            "links": [l.to_dict() for l in self.links],
            "headings": self.headings,
            "paragraphs": self.paragraphs,
        }
    
    def summary(self) -> str:
        return (
            f"Page: {self.title}\n"
            f"  Buttons: {len(self.buttons)}\n"
            f"  Forms: {len(self.forms)}\n"
            f"  Links: {len(self.links)}\n"
            f"  Headings: {len(self.headings)}\n"
            f"  Paragraphs: {self.paragraphs}"
        )