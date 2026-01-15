import pytest
from bs4 import BeautifulSoup
from src.browser.analyzer import PageAnalyzer
from src.browser.models import Button, Form, Input, Link, PageStructure
from src.browser.selector_generator import SelectorGenerator


class TestSelectorGenerator:
    """Test selector generation strategy"""
    
    def test_id_strategy(self):
        """ID should be preferred (99% stable)"""
        html = '<button id="submit-button">Submit</button>'
        soup = BeautifulSoup(html, "lxml")
        button = soup.find("button")
        
        selector, score = SelectorGenerator.generate(button)
        assert selector == "#submit-button"
        assert score == 99
    
    def test_class_strategy(self):
        """Classes should be second choice (90% stable)"""
        html = '<button class="btn btn-primary">Submit</button>'
        soup = BeautifulSoup(html, "lxml")
        button = soup.find("button")
        
        selector, score = SelectorGenerator.generate(button)
        assert "btn" in selector
        assert score == 90
    
    def test_reject_dynamic_classes(self):
        """Should reject React/Vue generated classes"""
        html = '<button class="jsx-12345 sc-abcd">Click</button>'
        soup = BeautifulSoup(html, "lxml")
        button = soup.find("button")
    
        selector, score = SelectorGenerator.generate(button)
        # Should fallback to nth-child or simple button selector
        assert "nth-child" in selector or selector == "button" or selector == "body > button"
    
    def test_attribute_strategy_input(self):
        """Form inputs should use name + type attributes"""
        html = '<input type="text" name="username">'
        soup = BeautifulSoup(html, "lxml")
        inp = soup.find("input")
        
        selector, score = SelectorGenerator.generate(inp)
        assert "name='username'" in selector
        assert score == 85
    
    def test_href_strategy_link(self):
        """Links should use href attribute"""
        html = '<a href="/home">Home</a>'
        soup = BeautifulSoup(html, "lxml")
        link = soup.find("a")
        
        selector, score = SelectorGenerator.generate(link)
        assert "href='/home'" in selector
    
    def test_nth_child_fallback(self):
        """Should fallback to nth-child when no better option"""
        html = '<div><p></p><button>Click</button></div>'
        soup = BeautifulSoup(html, "lxml")
        button = soup.find("button")
        
        selector, score = SelectorGenerator.generate(button)
        assert "nth-child" in selector or score == 40


class TestButtonExtraction:
    """Test button extraction"""
    
    def test_extract_single_button(self):
        """Should extract single button"""
        html = """
        <html>
            <body>
                <button id="submit">Submit</button>
            </body>
        </html>
        """
        analyzer = PageAnalyzer(html)
        buttons = analyzer.extract_buttons()
        
        assert len(buttons) == 1
        assert buttons[0].text == "Submit"
        assert "#submit" in buttons[0].selector
    
    def test_extract_multiple_buttons(self):
        """Should extract multiple buttons"""
        html = """
        <html>
            <body>
                <button>Sign In</button>
                <button>Reset</button>
                <button type="submit">Submit</button>
            </body>
        </html>
        """
        analyzer = PageAnalyzer(html)
        buttons = analyzer.extract_buttons()
        
        assert len(buttons) == 3
        assert buttons[0].text == "Sign In"
    
    def test_button_with_aria_label(self):
        """Should extract aria-label as button text"""
        html = '<button aria-label="Close menu">✕</button>'
        analyzer = PageAnalyzer(html)
        buttons = analyzer.extract_buttons()
        
        assert len(buttons) == 1
        assert buttons[0].text == "Close menu"
    
    def test_button_preserves_type(self):
        """Should preserve button type"""
        html = '<button type="submit">Submit</button>'
        analyzer = PageAnalyzer(html)
        buttons = analyzer.extract_buttons()
        
        assert buttons[0].type == "submit"
    
    def test_button_detects_parent_form(self):
        """Should detect parent form"""
        html = """
        <form id="login-form">
            <input type="text" name="user">
            <button type="submit">Login</button>
        </form>
        """
        analyzer = PageAnalyzer(html)
        buttons = analyzer.extract_buttons()
        
        assert buttons[0].form_selector is not None


class TestFormExtraction:
    """Test form extraction"""
    
    def test_extract_single_form(self):
        """Should extract single form"""
        html = """
        <form id="search" action="/search" method="GET">
            <input type="text" name="q">
            <button type="submit">Search</button>
        </form>
        """
        analyzer = PageAnalyzer(html)
        forms = analyzer.extract_forms()
        
        assert len(forms) == 1
        assert forms[0].action == "/search"
        assert forms[0].method == "GET"
    
    def test_extract_form_inputs(self):
        """Should extract all inputs from form"""
        html = """
        <form id="login">
            <input type="text" name="username" placeholder="Username">
            <input type="password" name="password">
            <textarea name="bio"></textarea>
            <select name="country"></select>
        </form>
        """
        analyzer = PageAnalyzer(html)
        forms = analyzer.extract_forms()
        
        assert len(forms[0].inputs) == 4
        assert forms[0].inputs[0].type == "text"
        assert forms[0].inputs[1].type == "password"
    
    def test_input_with_required_attribute(self):
        """Should detect required inputs"""
        html = '<input type="email" name="email" required>'
        analyzer = PageAnalyzer(html)
        analyzer.soup = BeautifulSoup(
            f'<form>{html}</form>', "lxml"
        )
        inputs = analyzer._extract_form_inputs(analyzer.soup.find("form"))
        
        assert inputs[0].required is True
    
    def test_input_preserves_placeholder(self):
        """Should preserve placeholder text"""
        html = '<input type="text" name="search" placeholder="Search...">'
        analyzer = PageAnalyzer(html)
        analyzer.soup = BeautifulSoup(
            f'<form>{html}</form>', "lxml"
        )
        inputs = analyzer._extract_form_inputs(analyzer.soup.find("form"))
        
        assert inputs[0].placeholder == "Search..."


class TestLinkExtraction:
    """Test link extraction"""
    
    def test_extract_single_link(self):
        """Should extract single link"""
        html = '<a href="/home">Home</a>'
        analyzer = PageAnalyzer(html)
        links = analyzer.extract_links()
        
        assert len(links) == 1
        assert links[0].text == "Home"
        assert links[0].href == "/home"
    
    def test_extract_multiple_links(self):
        """Should extract multiple links"""
        html = """
        <a href="/">Home</a>
        <a href="/about">About</a>
        <a href="/contact">Contact</a>
        """
        analyzer = PageAnalyzer(html)
        links = analyzer.extract_links()
        
        assert len(links) == 3
    
    def test_link_title_attribute(self):
        """Should preserve title attribute"""
        html = '<a href="/docs" title="Documentation">Docs</a>'
        analyzer = PageAnalyzer(html)
        links = analyzer.extract_links()
        
        assert links[0].title == "Documentation"
    
    def test_skip_links_without_text(self):
        """Should skip links without text"""
        html = """
        <a href="/page1">Link 1</a>
        <a href="/page2"></a>
        <a href="/page3">Link 3</a>
        """
        analyzer = PageAnalyzer(html)
        links = analyzer.extract_links()
        
        assert len(links) == 2


class TestPageStructure:
    """Test complete page analysis"""
    
    def test_get_page_structure_complete(self):
        """Should analyze complete page structure"""
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Welcome</h1>
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
                <form id="contact">
                    <input type="text" name="name">
                    <button type="submit">Send</button>
                </form>
                <a href="/home">Home</a>
            </body>
        </html>
        """
        analyzer = PageAnalyzer(html, page_url="https://example.com")
        structure = analyzer.get_page_structure()
        
        assert structure.title == "Test Page"
        assert structure.url == "https://example.com"
        assert len(structure.forms) == 1
        assert len(structure.buttons) == 1
        assert len(structure.links) == 1
        assert len(structure.headings) == 1
        assert structure.paragraphs == 2
    
    def test_page_structure_to_dict(self):
        """Should convert to dict for JSON serialization"""
        html = '<button id="btn">Click</button>'
        analyzer = PageAnalyzer(html)
        structure = analyzer.get_page_structure()
        
        data = structure.to_dict()
        assert isinstance(data, dict)
        assert "title" in data
        assert "buttons" in data
    
    def test_page_summary(self):
        """Should generate summary string"""
        html = '<button>Test</button>'
        analyzer = PageAnalyzer(html)
        structure = analyzer.get_page_structure()
        
        summary = structure.summary()
        assert "Buttons: 1" in summary
        assert "Forms: 0" in summary


class TestDataModels:
    """Test data model serialization"""
    
    def test_button_to_dict(self):
        """Button should serialize to dict"""
        button = Button(text="Click", selector="#btn")
        data = button.to_dict()
        
        assert data["text"] == "Click"
        assert data["selector"] == "#btn"
    
    def test_form_to_dict_with_inputs(self):
        """Form should serialize inputs"""
        form = Form(
            selector="#form",
            inputs=[
                Input(name="email", type="email", selector="input[name='email']")
            ]
        )
        data = form.to_dict()
        
        assert len(data["inputs"]) == 1
        assert data["inputs"][0]["name"] == "email"
    
    def test_page_structure_serialization(self):
        """PageStructure should fully serialize"""
        structure = PageStructure(
            title="Test",
            url="https://test.com",
            buttons=[Button(text="OK", selector="#ok")],
            paragraphs=5
        )
        data = structure.to_dict()
        
        assert data["title"] == "Test"
        assert len(data["buttons"]) == 1
        assert data["paragraphs"] == 5