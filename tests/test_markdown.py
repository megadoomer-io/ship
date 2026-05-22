from ship import markdown


def test_renders_basic_markdown():
    result = markdown.render("# Hello\n\nSome **bold** text.")
    assert "<h1>Hello</h1>" in result
    assert "<strong>bold</strong>" in result


def test_strips_yaml_frontmatter():
    text = "---\ntitle: Test\ntags: [foo]\n---\n\n# Content"
    result = markdown.render(text)
    assert "title: Test" not in result
    assert "<h1>Content</h1>" in result


def test_converts_wiki_links_to_bold():
    result = markdown.render("See [[My Note]] for details.")
    assert "[[" not in result
    assert "<strong>My Note</strong>" in result


def test_converts_wiki_links_with_alias():
    result = markdown.render("See [[path/to/note|the note]] for details.")
    assert "<strong>the note</strong>" in result
    assert "path/to/note" not in result


def test_converts_tags_to_styled_spans():
    result = markdown.render("Tagged with #project/ship here.")
    assert '<span class="tag">#project/ship</span>' in result


def test_does_not_convert_hash_in_headings():
    result = markdown.render("# Heading")
    assert '<span class="tag">' not in result


def test_renders_tables():
    text = "| A | B |\n|---|---|\n| 1 | 2 |"
    result = markdown.render(text)
    assert "<table>" in result
    assert "<td>1</td>" in result


def test_renders_task_lists():
    text = "- [x] Done\n- [ ] Not done"
    result = markdown.render(text)
    assert 'type="checkbox"' in result


def test_renders_links():
    result = markdown.render("[click here](https://example.com)")
    assert 'href="https://example.com"' in result


def test_preserves_code_blocks():
    text = "```python\nprint('hello')\n```"
    result = markdown.render(text)
    assert "print(" in result
