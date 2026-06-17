(function () {
    'use strict';

    var ENTRY_SELECTOR = '.entry-card, [data-filterable]';
    var SECTION_SELECTOR = 'details.section-collapse';
    var HIDE_CLASS = 'filter-hide';
    var FILTER_ACTIVE_CLASS = 'filter-active';
    var DEBOUNCE_MS = 60;

    var input = document.getElementById('filter-input');
    var status = document.querySelector('[data-filter-status]');
    var clearBtn = document.querySelector('[data-filter-clear]');
    if (!input) return;

    // CSS Custom Highlight API for term highlighting. Falls back gracefully —
    // filter still works on browsers without Highlight (older Firefox).
    var hlSupported = typeof Highlight !== 'undefined' && CSS && CSS.highlights;
    var highlight = hlSupported ? new Highlight() : null;
    if (hlSupported) CSS.highlights.set('ship-filter-match', highlight);

    var entries = [];
    var sections = [];
    // Map<details, boolean> — open state before filter took over
    var savedOpenState = new Map();
    var filterActive = false;
    var debounceTimer = null;

    function indexEntries() {
        entries = [];
        document.querySelectorAll(ENTRY_SELECTOR).forEach(function (el) {
            entries.push({
                el: el,
                text: (el.textContent || '').toLowerCase()
            });
        });
        sections = Array.prototype.slice.call(document.querySelectorAll(SECTION_SELECTOR));
    }

    function parseTerms(q) {
        // AND of whitespace-separated terms. Quoted phrases treated as one term.
        var terms = [];
        var re = /"([^"]+)"|(\S+)/g;
        var m;
        while ((m = re.exec(q)) !== null) {
            var t = (m[1] || m[2] || '').toLowerCase();
            if (t) terms.push(t);
        }
        return terms;
    }

    function entryMatches(entry, terms) {
        for (var i = 0; i < terms.length; i++) {
            if (entry.text.indexOf(terms[i]) === -1) return false;
        }
        return true;
    }

    function saveSectionState() {
        savedOpenState.clear();
        sections.forEach(function (s) { savedOpenState.set(s, s.open); });
    }

    function restoreSectionState() {
        sections.forEach(function (s) {
            if (savedOpenState.has(s)) s.open = savedOpenState.get(s);
            s.classList.remove(HIDE_CLASS);
        });
    }

    function clearAllHides() {
        entries.forEach(function (e) { e.el.classList.remove(HIDE_CLASS); });
        sections.forEach(function (s) { s.classList.remove(HIDE_CLASS); });
    }

    function clearHighlights() {
        if (highlight) highlight.clear();
    }

    // Walk text nodes inside `root` and add a Range to the highlight for each
    // occurrence of any term. Skips script/style nodes so we don't highlight
    // raw CSS or JS sources.
    function highlightMatches(root, terms) {
        if (!highlight) return;
        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
            acceptNode: function (node) {
                var p = node.parentNode;
                if (!p) return NodeFilter.FILTER_REJECT;
                var tag = p.nodeName;
                if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') {
                    return NodeFilter.FILTER_REJECT;
                }
                if (!node.nodeValue || !node.nodeValue.trim()) {
                    return NodeFilter.FILTER_REJECT;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        });
        var node;
        while ((node = walker.nextNode())) {
            var text = node.nodeValue.toLowerCase();
            for (var i = 0; i < terms.length; i++) {
                var term = terms[i];
                var idx = text.indexOf(term);
                while (idx !== -1) {
                    var range = document.createRange();
                    range.setStart(node, idx);
                    range.setEnd(node, idx + term.length);
                    highlight.add(range);
                    idx = text.indexOf(term, idx + term.length);
                }
            }
        }
    }

    function applyFilter(query) {
        var terms = parseTerms(query);
        clearHighlights();
        if (terms.length === 0) {
            if (filterActive) {
                clearAllHides();
                restoreSectionState();
                filterActive = false;
                document.body.classList.remove(FILTER_ACTIVE_CLASS);
            }
            if (status) status.textContent = '';
            if (clearBtn) clearBtn.hidden = true;
            return;
        }

        if (!filterActive) {
            saveSectionState();
            filterActive = true;
            document.body.classList.add(FILTER_ACTIVE_CLASS);
        }
        if (clearBtn) clearBtn.hidden = false;

        var matches = 0;
        // Pass 1: mark entries hidden/visible, highlight terms in visible ones
        entries.forEach(function (entry) {
            if (entryMatches(entry, terms)) {
                entry.el.classList.remove(HIDE_CLASS);
                matches++;
                highlightMatches(entry.el, terms);
            } else {
                entry.el.classList.add(HIDE_CLASS);
            }
        });

        // Pass 2: open sections whose textContent matches any term, close the
        // rest. Matching against textContent (not just filterable descendants)
        // means sections containing matching markdown lists / paragraphs also
        // stay open — e.g. nested plan sections inside an entry-card.
        // Sections themselves stay visible — the summary header remains so
        // document structure is preserved. Original open/closed state is
        // saved on first activation and restored on clear.
        sections.forEach(function (section) {
            var text = (section.textContent || '').toLowerCase();
            var sectionMatches = false;
            for (var i = 0; i < terms.length; i++) {
                if (text.indexOf(terms[i]) !== -1) {
                    sectionMatches = true;
                    break;
                }
            }
            section.open = sectionMatches;
        });

        if (status) {
            status.textContent = matches === 1 ? '1 match' : matches + ' matches';
        }
    }

    function debouncedApply() {
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () {
            applyFilter(input.value);
        }, DEBOUNCE_MS);
    }

    input.addEventListener('input', debouncedApply);

    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            input.value = '';
            applyFilter('');
            input.focus();
        });
    }

    // '/' hotkey: focus filter unless already in an editable field.
    document.addEventListener('keydown', function (e) {
        if (e.key !== '/') return;
        if (e.ctrlKey || e.metaKey || e.altKey) return;
        var t = e.target;
        if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
        e.preventDefault();
        input.focus();
        input.select();
    });

    // Escape clears the filter when input is focused.
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            input.value = '';
            applyFilter('');
            input.blur();
        }
    });

    // Re-index after infinite scroll appends new cards.
    document.addEventListener('ship:content-appended', function () {
        indexEntries();
        if (filterActive) applyFilter(input.value);
    });

    indexEntries();
})();
