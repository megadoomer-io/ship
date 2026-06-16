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


class TestRules:
    def test_matched_section_collapsed(self) -> None:
        html = "<h2>GSTACK REVIEW REPORT</h2><p>Long analysis</p>"
        result = collapse_sections(html, "plan")
        assert 'class="section-collapse section-h2">' in result
        assert " open" not in result.split("</summary>")[0]

    def test_matched_section_open(self) -> None:
        html = "<h2>Commitments</h2><p>Tasks</p>"
        result = collapse_sections(html, "plan")
        assert " open" in result.split("</summary>")[0]

    def test_unmatched_section_defaults_open(self) -> None:
        html = "<h2>Something New</h2><p>Content</p>"
        result = collapse_sections(html, "plan")
        assert " open" in result.split("</summary>")[0]

    def test_substring_matching(self) -> None:
        html = "<h2>Trends vs W23</h2><p>Table</p>"
        result = collapse_sections(html, "retro")
        assert " open" not in result.split("</summary>")[0]

    def test_case_insensitive_matching(self) -> None:
        html = "<h2>commitments</h2><p>Tasks</p>"
        result = collapse_sections(html, "plan")
        assert " open" in result.split("</summary>")[0]


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

    def test_unknown_content_type_returns_unchanged(self) -> None:
        html = "<h2>Section</h2><p>Body</p>"
        assert collapse_sections(html, "unknown_type") == html

    def test_empty_content_type_returns_unchanged(self) -> None:
        html = "<h2>Section</h2><p>Body</p>"
        assert collapse_sections(html, "") == html


class TestContentTypes:
    def test_retro_highlights_open(self) -> None:
        html = "<h2>Highlights</h2><p>Good stuff</p>"
        result = collapse_sections(html, "retro")
        assert " open" in result.split("</summary>")[0]

    def test_weekly_by_project_collapsed(self) -> None:
        html = "<h2>By Project</h2><p>Details</p>"
        result = collapse_sections(html, "weekly")
        assert " open" not in result.split("</summary>")[0]

    def test_plan_multiple_sections_mixed_state(self) -> None:
        html = (
            "<h2>Commitments</h2><p>Tasks</p><h2>Deferred</h2><p>Later</p><h2>GSTACK REVIEW REPORT</h2><p>Analysis</p>"
        )
        result = collapse_sections(html, "plan")
        details_blocks = result.split("<details")
        assert len(details_blocks) == 4  # 1 preamble (empty) + 3 details
        assert " open" in details_blocks[1]  # Commitments
        assert " open" not in details_blocks[2]  # Deferred
        assert " open" not in details_blocks[3]  # GSTACK REVIEW REPORT
