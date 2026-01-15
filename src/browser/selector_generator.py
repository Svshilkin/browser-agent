from typing import Optional
from bs4 import Tag
import logging

logger = logging.getLogger(__name__)


class SelectorGenerator:
    """Generate CSS selectors with robustness priority"""
    
    # Stability score for different selector types
    STABILITY_SCORES = {
        "id": 99,           # Most stable
        "class": 90,        # Stable if not generated
        "attribute": 85,    # Stable for form inputs
        "nth_child": 40,    # Fragile - breaks on DOM changes
    }
    
    # Classes that indicate React/Vue/dynamic generation
    DYNAMIC_CLASS_PATTERNS = [
        "jsx-", "sc-", "vf-", "v-", "_", "__",
        "hash", "random", "tmp", "tmp_", "component"
    ]
    
    @staticmethod
    def generate(element: Tag) -> tuple[str, int]:
        """
        Generate selector with robustness score
        Returns: (selector_string, stability_score)
        """
        # Strategy 1: ID (99% stable)
        if element.has_attr("id") and element.get("id"):
            element_id = element.get("id")
            if SelectorGenerator._is_valid_id(element_id):
                return f"#{element_id}", SelectorGenerator.STABILITY_SCORES["id"]
        
        # Strategy 2: Classes (90% stable if not dynamic)
        classes = element.get("class", [])
        if isinstance(classes, list) and classes:
            stable_classes = SelectorGenerator._filter_stable_classes(classes)
            if stable_classes:
                class_selector = ".".join(stable_classes)
                tag = element.name or "div"
                selector = f"{tag}.{class_selector}"
                return selector, SelectorGenerator.STABILITY_SCORES["class"]
        
        # Strategy 3: Attributes (85% stable - for form inputs)
        if element.name in ["input", "textarea", "select"]:
            if element.has_attr("name"):
                name = element.get("name")
                elem_type = element.get("type", "text")
                selector = f"{element.name}[name='{name}'][type='{elem_type}']"
                return selector, SelectorGenerator.STABILITY_SCORES["attribute"]
        
        # Strategy 4: Button/link specific attributes
        if element.name == "button":
            if element.has_attr("type"):
                btn_type = element.get("type")
                selector = f"button[type='{btn_type}']"
                return selector, SelectorGenerator.STABILITY_SCORES["attribute"]
        
        if element.name == "a":
            if element.has_attr("href"):
                href = element.get("href")
                selector = f"a[href='{href}']"
                return selector, SelectorGenerator.STABILITY_SCORES["attribute"]
        
        # Strategy 5: Fallback to nth-child (40% stable)
        nth_child_selector = SelectorGenerator._generate_nth_child_path(element)
        return nth_child_selector, SelectorGenerator.STABILITY_SCORES["nth_child"]
    
    @staticmethod
    def _is_valid_id(element_id: str) -> bool:
        """Check if ID is valid and not auto-generated"""
        # Reject numeric-only or hash-like IDs
        if element_id.isdigit() or len(element_id) > 50:
            return False
        # Reject common dynamic patterns
        dynamic_patterns = ["react-", "vue-", "__", "tmp", "hash"]
        for pattern in dynamic_patterns:
            if pattern in element_id.lower():
                return False
        return True
    
    @staticmethod
    def _filter_stable_classes(classes: list) -> list:
        """Filter out dynamic/generated classes"""
        stable = []
        for cls in classes:
            # Skip dynamic patterns
            is_dynamic = any(pattern in cls.lower() for pattern in SelectorGenerator.DYNAMIC_CLASS_PATTERNS)
            if not is_dynamic and cls:
                stable.append(cls)
        return stable[:3]  # Max 3 classes
    
    @staticmethod
    def _generate_nth_child_path(element: Tag) -> str:
        """Generate nth-child selector as last resort"""
        path = []
        current = element
        
        while current and current.name and current.name != "html":
            # Find position among siblings
            parent = current.parent
            if not parent:
                break
            
            siblings = [s for s in parent.children if hasattr(s, 'name') and s.name]
            same_tag_siblings = [s for s in siblings if s.name == current.name]
            
            if same_tag_siblings:
                position = same_tag_siblings.index(current) + 1
                if len(same_tag_siblings) > 1:
                    path.insert(0, f"{current.name}:nth-child({position})")
                else:
                    path.insert(0, current.name)
            
            current = parent
        
        return " > ".join(path) if path else "body"