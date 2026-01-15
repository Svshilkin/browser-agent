"""Browser management module"""

from .manager import BrowserManager, BrowserError
from .analyzer import PageAnalyzer
from .models import Button, Form, Input, Link, PageStructure
from .selector_generator import SelectorGenerator

__all__ = [
    "BrowserManager",
    "PageAnalyzer",
    "Button",
    "Form",
    "Input",
    "Link",
    "PageStructure",
    "SelectorGenerator",
    "BrowserError",
]