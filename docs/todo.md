# UX Maturity Analysis - Todo List

## Active Tasks

### Visual Polish - Current Session
- [ ] Fix visual analysis section width (label truncation issue)
- [ ] Improve plotly graph labeling for clarity
- [ ] Review final visuals with user
- [ ] Update documentation with any final changes

---

## Pending Tasks

### Phase 2: Pipeline Integration
- [ ] Make CSS build automatic in `HTMLReportGenerator`
  - Currently: manual `python3 scripts/build_css.py`
  - Need: auto-build when generating reports
- [ ] Verify pipeline produces identical output to example report
- [ ] Test with real analysis data (not just sample data)

### Phase 3: GitHub Actions
- [ ] Create `.github/workflows/deploy.yml`
- [ ] Configure Netlify deployment
- [ ] Set up domain/URL

### Phase 4: Testing
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile testing
- [ ] Performance optimization

---

## Completed Tasks

### Session: Feb 25, 2026
- [x] Fixed screenshot visibility issue
  - Changed `competitor_name` → `site_name` in regeneration script
  - Changed `screenshots` → `screenshot_metadata`
  - Added relative→absolute path conversion
- [x] Created project documentation
  - `docs/frontend-workflow-summary.md` - Complete context reference
  - `docs/plan.md` - Project roadmap
  - `docs/todo.md` - Task tracking

### Earlier Sessions
- [x] Created modular Sass architecture (7 partial files)
- [x] Built CSS pipeline (Python + Shell scripts)
- [x] Removed inline CSS from templates
- [x] Fixed responsive transitions (added `transition` properties)
- [x] Fixed lightbox panning (event handling)
- [x] Fixed section expansion/collapse (event propagation)
- [x] Annotations: left-aligned, stacked vertically
- [x] Evidence: moved into competitor sections only
- [x] Created sample data (`basket_pages_example.json`)
- [x] Created regeneration script

---

## Quick Commands

```bash
# Build CSS
python3 scripts/build_css.py

# Regenerate example report
python3 scripts/regenerate_example_report.py

# View report
# http://localhost:8888/resources-basket-pages-example-report.html
```

---

## Notes

- Example report: `output/resources-basket-pages-example-report.html`
- Screenshot images: `output/screenshots/desktop.png`, `output/screenshots/mobile.png`
- CSS output: `output/css/main.css` (~20KB)

**Workflow:** Modify CSS → Rebuild → Regenerate → Review → Repeat
