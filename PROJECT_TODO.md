# Project Todo - Code Quality & Maintainability Refactoring

**Status:** Active
**Last Updated:** 2026-02-26
**Context:** Approach 1 - Refactor & Consolidate

---

## Legend
- [ ] Not started
- [x] Completed
- [~] In progress
- [!] Blocked
- [>] Deferred

---

## Section 1: CSS Duplication Elimination

- [x] Audit CSS for duplicate classes and patterns
- [x] Consolidate `.chart` styles (appears in _sections.scss and _mobile.scss)
- [ ] Create shared component patterns for repeated styles
- [ ] Remove orphaned/dead CSS rules
- [ ] Test all pages after CSS consolidation

**Priority:** High
**Estimated:** 2 hours

---

## Section 2: Template Component Extraction

- [x] Audit templates for repeated markup (sidebar, header, theme toggle)
- [x] Create `_theme_toggle.jinja2` partial
- [x] Create `_brand.jinja2` partial
- [ ] Create `_sidebar.jinja2` partial
- [ ] Create `_header.jinja2` partial
- [ ] Create `_footer.jinja2` partial
- [x] Update index.html.jinja2 to use partials
- [x] Update report.html.jinja2 to use partials
- [ ] Test all templates with partials

**Priority:** High
**Estimated:** 3 hours

---

## Section 3: Developer Onboarding Guide

- [x] Create `docs/ONBOARDING.md` with:
  - [x] Project structure overview
  - [x] How to run analysis
  - [x] How to add new page types
  - [x] How to modify reports
  - [x] Common troubleshooting steps
- [x] Create `docs/COMMON_TASKS.md` (add report type, change colors, deploy)
- [ ] Add quick reference links to README

**Priority:** Medium
**Estimated:** 1.5 hours

---

## Section 4: Code Quality Standards

- [ ] Install and configure flake8
- [ ] Install and configure black
- [ ] Install and configure isort
- [ ] Set up pre-commit hooks
- [ ] Create `.flake8` config (max line length = 100)
- [ ] Create `.black` config if needed
- [ ] Run initial linting on entire codebase
- [ ] Fix critical linting issues
- [ ] Document linting standards in docs/

**Priority:** Medium
**Estimated:** 2 hours

---

## Section 5: Index HTML Script Consolidation

- [ ] Audit output/index.html for hardcoded values
- [ ] Determine if it should use template system
- [ ] Update index.html.jinja2 if changes needed
- [ ] Update generate_index.py script
- [ ] Test index generation

**Priority:** Medium
**Estimated:** 1 hour

---

## Section 6: Documentation Updates

- [ ] Update ARCHITECTURE.md with recent features:
  - [ ] Theme toggle
  - [ ] Responsive fixes
  - [ ] Live chart resize
  - [ ] Accessibility improvements (WCAG AA)
- [ ] Verify all docs/ files are up to date
- [ ] Create CHANGELOG entry for v1.7.0 (refactoring)
- [ ] Update README with new development workflow

**Priority:** Low
**Estimated:** 1 hour

---

## Completed Today

- [x] Fixed report card layout (class naming conflict)
- [x] Fixed index.html template to use `.index-report-card`
- [x] Fixed report card CSS structure
- [x] Increased font sizes for WCAG AA compliance
- [x] Fixed light theme accent colors for contrast
- [x] Added live chart resize with Plotly.Plots.resize()
- [x] Moved radar chart legend below chart
- [x] Fixed theme toggle in report template

---

## Notes

**CSS Duplication Found:**
- `.chart` class appears in both `_sections.scss` and `_mobile.scss`
- **Assessment:** INTENTIONAL - this is correct responsive design pattern
  - `_sections.scss` contains base styles
  - `_mobile.scss` contains media query overrides
  - This is proper SCSS pattern, not duplication

**Other Observations:**
- No obvious orphaned CSS rules
- Chart styles use design tokens correctly
- Theme toggle appears in correct locations

**Key Files Modified Today:**
- css/_variables.scss (font sizes, accent colors)
- css/_components.scss (report card styles)
- css/_sections.scss (insights grid, rankings)
- css/_mobile.scss (chart responsive styles)
- templates/report.html.jinja2 (theme toggle)
- templates/index.html.jinja2 (class naming)
- src/utils/html_report_generator.py (radar legend, resize JS)

---

## Recovery Instructions

**If picking up after API limit:**

1. Check `[~] In progress` items to see current state
2. Read **Completed Today** section to understand context
3. Read **Notes** section for any blockers or decisions made
4. Continue with next `[ ]` task in current section

**Example recovery:**
```
[ ] Audit CSS for duplicate classes
[~] Create shared component patterns  <-- API limit hit here
```
→ Resume with: Review what was found in audit, continue with shared patterns

---

## Version Tracking

- **Todo Version:** 1.0
- **Project Version:** 1.6.0
- **Target Release:** v1.7.0 (after refactoring)
