from typing import Optional, List
from bs4 import BeautifulSoup, Tag
import logging
from src.browser.models import Button, Form, Input, Link, PageStructure
from src.browser.selector_generator import SelectorGenerator

logger = logging.getLogger(__name__)


class PageAnalyzer:
    """Analyze HTML page structure and extract interactive elements"""
    
    def __init__(self, html_content: str, page_url: str = ""):
        """
        Initialize analyzer with HTML content
        
        Args:
            html_content: HTML string to analyze
            page_url: Current page URL (for relative link resolution)
        """
        self.html_content = html_content
        self.page_url = page_url
        self.soup = BeautifulSoup(html_content, "lxml")
    
    def get_page_structure(self) -> PageStructure:
        """Extract complete page structure"""
        logger.debug("Analyzing page structure...")
        
        title = self._extract_title()
        buttons = self.extract_buttons()
        forms = self.extract_forms()
        links = self.extract_links()
        headings = self._extract_headings()
        paragraphs = self._count_paragraphs()
        
        structure = PageStructure(
            title=title,
            url=self.page_url,
            buttons=buttons,
            forms=forms,
            links=links,
            headings=headings,
            paragraphs=paragraphs,
        )
        
        logger.info(f"Page analyzed: {structure.summary()}")
        return structure
    
    def extract_buttons(self) -> List[Button]:
        """Extract all buttons from page"""
        logger.debug("Extracting buttons...")
        buttons = []
    
        # Find all button elements
        button_elements = self.soup.find_all("button")
        
        for btn in button_elements:
            try:
                # First try aria-label for accessibility text
                text = btn.get("aria-label", "").strip()
                if not text:
                    # Fall back to visible text
                    text = btn.get_text(strip=True)
                
                if not text:
                    continue  # Skip buttons with no text
                
                selector, _score = SelectorGenerator.generate(btn)
                btn_type = btn.get("type", "button")
                
                # Find parent form if exists
                form_parent = btn.find_parent("form")
                form_selector = None
                if form_parent:
                    form_selector, _ = SelectorGenerator.generate(form_parent)
                
                button = Button(
                    text=text,
                    selector=selector,
                    type=btn_type,
                    form_selector=form_selector,
                )
                buttons.append(button)
                logger.debug(f"  Found button: {text} -> {selector}")
            
            except Exception as e:
                logger.warning(f"Error extracting button: {e}")
        
        return buttons
    
    def extract_forms(self) -> List[Form]:
        """Extract all forms and their inputs"""
        logger.debug("Extracting forms...")
        forms = []
        
        form_elements = self.soup.find_all("form")
        
        for form in form_elements:
            try:
                selector, _score = SelectorGenerator.generate(form)
                action = form.get("action", "")
                method = form.get("method", "POST").upper()
                
                # Extract inputs
                inputs = self._extract_form_inputs(form)
                
                form_obj = Form(
                    selector=selector,
                    action=action,
                    method=method,
                    inputs=inputs,
                )
                forms.append(form_obj)
                logger.debug(f"  Found form: {selector} ({len(inputs)} inputs)")
            
            except Exception as e:
                logger.warning(f"Error extracting form: {e}")
        
        return forms
    
    def _extract_form_inputs(self, form: Tag) -> List[Input]:
        """Extract input fields from a form"""
        inputs = []
        
        # Find all input, textarea, select elements
        input_elements = form.find_all(["input", "textarea", "select"])
        
        for inp in input_elements:
            try:
                name = inp.get("name")
                if not name:
                    continue  # Skip unnamed inputs
                
                inp_type = inp.get("type", "text")
                selector, _score = SelectorGenerator.generate(inp)
                value = inp.get("value", "")
                placeholder = inp.get("placeholder", "")
                required = inp.has_attr("required")
                
                input_obj = Input(
                    name=name,
                    type=inp_type,
                    selector=selector,
                    value=value if value else None,
                    placeholder=placeholder if placeholder else None,
                    required=required,
                )
                inputs.append(input_obj)
                logger.debug(f"    Input: {name} ({inp_type})")
            
            except Exception as e:
                logger.warning(f"Error extracting input: {e}")
        
        return inputs
    
    def extract_links(self) -> List[Link]:
        """Extract all links from page"""
        logger.debug("Extracting links...")
        links = []
        
        link_elements = self.soup.find_all("a")
        
        for link in link_elements:
            try:
                text = link.get_text(strip=True)
                href = link.get("href", "")
                
                if not href or not text:
                    continue  # Skip links without href or text
                
                selector, _score = SelectorGenerator.generate(link)
                title = link.get("title", "")
                
                link_obj = Link(
                    text=text,
                    href=href,
                    selector=selector,
                    title=title if title else None,
                )
                links.append(link_obj)
                logger.debug(f"  Found link: {text} -> {href}")
            
            except Exception as e:
                logger.warning(f"Error extracting link: {e}")
        
        return links
    
    def _extract_title(self) -> str:
        """Extract page title"""
        title_tag = self.soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        return "Untitled"
    
    def _extract_headings(self) -> List[str]:
        """Extract all headings from page"""
        headings = []
        for h in self.soup.find_all(["h1", "h2", "h3"]):
            text = h.get_text(strip=True)
            if text:
                headings.append(text)
        return headings[:10]  # Max 10 headings
    
    def _count_paragraphs(self) -> int:
        """Count paragraphs on page"""
        return len(self.soup.find_all("p"))