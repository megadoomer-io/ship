from ship.collapse import collapse_sections


class TestBasicWrapping:
    def test_two_h2_sections(self) -> None:
        html = "<h2>First</h2><p>Content A</p><h2>Second</h2><p>Content B</p>"
        result = collapse_sections(html, "plan")
        assert result.count("<details") == 2
        assert result.count("</details>") == 2
        assert "<summary>First</summary>" in result
        assert "<summary>Second</summary>" in result

    def test_content_preserved_in_sections(self) -> None:
        html = "<h2>Title</h2><p>Body text</p><ul><li>item</li></ul>"
        result = collapse_sections(html, "plan")
        assert "<p>Body text</p>" in result
        assert "<ul><li>item</li></ul>" in result

    def test_section_content_wrapped_in_div(self) -> None:
        html = "<h2>Title</h2><p>Body</p>"
        result = collapse_sections(html, "plan")
        assert '<div class="section-content">' in result
        assert "</div></details>" in result


class TestFirstSectionOnly:
    def test_first_h2_is_open(self) -> None:
        html = "<h2>First</h2><p>A</p><h2>Second</h2><p>B</p><h2>Third</h2><p>C</p>"
        result = collapse_sections(html, "plan")
        details = result.split("<details")
        assert " open" in details[1]
        assert " open" not in details[2]
        assert " open" not in details[3]

    def test_first_h3_in_first_h2_is_open(self) -> None:
        html = "<h2>Parent</h2><h3>Child1</h3><p>A</p><h3>Child2</h3><p>B</p>"
        result = collapse_sections(html, "plan")
        h3_blocks = [s for s in result.split("<details") if "section-h3" in s]
        assert len(h3_blocks) == 2
        assert " open" in h3_blocks[0]
        assert " open" not in h3_blocks[1]

    def test_h3_in_second_h2_all_collapsed(self) -> None:
        html = "<h2>First</h2><h3>Sub1</h3><p>A</p><h2>Second</h2><h3>Sub2</h3><p>B</p><h3>Sub3</h3><p>C</p>"
        result = collapse_sections(html, "plan")
        second_h2_pos = result.index('data-section="second"')
        h3_after_second = result[second_h2_pos:]
        assert h3_after_second.count(" open") == 0

    def test_single_h2_is_open(self) -> None:
        html = "<h2>Only</h2><p>Content</p>"
        result = collapse_sections(html, "plan")
        assert " open" in result.split("</summary>")[0]


class TestNesting:
    def test_h3_nests_inside_h2(self) -> None:
        html = "<h2>Parent</h2><p>Intro</p><h3>Child</h3><p>Detail</p>"
        result = collapse_sections(html, "plan")
        assert "section-h2" in result
        assert "section-h3" in result
        h2_start = result.index("section-h2")
        h3_start = result.index("section-h3")
        assert h2_start < h3_start

    def test_h3_before_any_h2_goes_to_preamble(self) -> None:
        html = "<h3>Orphan</h3><p>Text</p><h2>Section</h2><p>Body</p>"
        result = collapse_sections(html, "plan")
        assert "<h3>Orphan</h3>" in result
        assert result.count("section-h2") == 1
        assert "section-h3" not in result

    def test_multiple_h3_under_one_h2(self) -> None:
        html = "<h2>Parent</h2><h3>A</h3><p>1</p><h3>B</h3><p>2</p>"
        result = collapse_sections(html, "plan")
        assert result.count("section-h3") == 2

    def test_h3_closes_when_new_h2_starts(self) -> None:
        html = "<h2>S1</h2><h3>Sub</h3><p>X</p><h2>S2</h2><p>Y</p>"
        result = collapse_sections(html, "plan")
        s2_pos = result.index("<summary>S2</summary>")
        sub_close = result.index("</details>", result.index("section-h3"))
        assert sub_close < s2_pos


class TestPreamble:
    def test_content_before_first_h2_passes_through(self) -> None:
        html = "<p>Preamble</p><h2>Section</h2><p>Body</p>"
        result = collapse_sections(html, "plan")
        assert result.startswith("<p>Preamble</p>")
        assert "section-h2" in result

    def test_h1_passes_through(self) -> None:
        html = "<h1>Title</h1><h2>Section</h2><p>Body</p>"
        result = collapse_sections(html, "plan")
        assert "<h1>Title</h1>" in result


class TestDataSectionAttribute:
    def test_h2_has_data_section_slug(self) -> None:
        html = "<h2>Commitments</h2><p>Tasks</p>"
        result = collapse_sections(html, "plan")
        assert 'data-section="commitments"' in result

    def test_h3_has_data_section_slug(self) -> None:
        html = "<h2>Parent</h2><h3>Ops &amp; Promotions</h3><p>Tasks</p>"
        result = collapse_sections(html, "plan")
        assert 'data-section="ops-&amp;-promotions"' in result

    def test_slug_truncated_at_60_chars(self) -> None:
        long_title = "A" * 100
        html = f"<h2>{long_title}</h2><p>Content</p>"
        result = collapse_sections(html, "plan")
        assert 'data-section="' + "a" * 60 + '"' in result


class TestInlineMarkup:
    def test_header_with_strong(self) -> None:
        html = "<h2>Shipped <strong>v2</strong></h2><p>Details</p>"
        result = collapse_sections(html, "plan")
        assert "<summary>Shipped <strong>v2</strong></summary>" in result

    def test_header_with_code(self) -> None:
        html = "<h2>The <code>main</code> branch</h2><p>Info</p>"
        result = collapse_sections(html, "plan")
        assert "<summary>The <code>main</code> branch</summary>" in result


class TestEdgeCases:
    def test_empty_string(self) -> None:
        assert collapse_sections("", "plan") == ""

    def test_no_headers(self) -> None:
        html = "<p>Just a paragraph</p>"
        assert collapse_sections(html, "plan") == html

    def test_none_content_type_returns_unchanged(self) -> None:
        html = "<h2>Section</h2><p>Body</p>"
        assert collapse_sections(html, None) == html

    def test_empty_content_type_returns_unchanged(self) -> None:
        html = "<h2>Section</h2><p>Body</p>"
        assert collapse_sections(html, "") == html

    def test_any_content_type_activates_collapsing(self) -> None:
        html = "<h2>Section</h2><p>Body</p>"
        result = collapse_sections(html, "anything")
        assert "section-collapse" in result
