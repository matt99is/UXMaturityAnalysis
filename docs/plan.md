# UX Maturity Analysis - Project Plan

## Phase 1: Visual Design Iteration (IN PROGRESS)

**Goal:** Refine the example report visuals until satisfied, then lock in as pipeline output.

### Current Focus
Working on `output/resources-basket-pages-example-report.html` as the reference implementation.

### 1.1 Fix Remaining Visual Issues
- [ ] Visual analysis section width - fix label truncation
- [ ] Plotly graph labeling - improve clarity

### 1.2 CSS Polish
- [ ] Review and refine all visual elements
- [ ] Ensure consistent spacing and typography
- [ ] Verify responsive behavior across breakpoints

### 1.3 Final Visual Review
- [ ] User approval of all visual elements
- [ ] Document any remaining edge cases

---

## Phase 2: Pipeline Integration

**Goal:** Ensure the pipeline produces identical output to the finalized example report.

### 2.1 Generator Integration
- [ ] Auto-build CSS on report generation (currently manual step)
- [ ] Verify `HTMLReportGenerator` produces same output as example script
- [ ] Test with real analysis data

### 2.2 Data Flow Verification
- [ ] Ensure screenshot paths resolve correctly in production
- [ ] Verify annotation data flows through pipeline
- [ ] Test evidence item rendering

---

## Phase 3: GitHub Actions Setup

**Goal:** Automate report generation and deployment.

### 3.1 Create Workflow
- [ ] Create `.github/workflows/deploy.yml`
- [ ] Set up build step (CSS compilation)
- [ ] Set up report generation step
- [ ] Configure artifact handling

### 3.2 Deployment Configuration
- [ ] Configure Netlify build settings
- [ ] Set up domain/URL
- [ ] Configure environment variables if needed

---

## Phase 4: Testing & Polish

### 4.1 Cross-Browser Testing
- [ ] Test in Chrome, Firefox, Safari
- [ ] Test on mobile devices
- [ ] Verify print layouts

### 4.2 Performance
- [ ] Optimize image loading
- [ ] Verify CSS size stays reasonable
- [ ] Check JavaScript performance

---

## Completed Work

### CSS Architecture (✓)
- [x] Modular Sass structure created
- [x] Design token system implemented
- [x] External CSS (not inline)
- [x] Build pipeline created

### Template Updates (✓)
- [x] Removed inline CSS from templates
- [x] Added external CSS links
- [x] Fixed event propagation bugs

### Visual Fixes (✓)
- [x] Responsive transitions (no snap effect)
- [x] Lightbox panning functionality
- [x] Annotations left-aligned and stacked
- [x] Evidence moved to competitor sections
- [x] Screenshot visibility fixed

### Documentation (✓)
- [x] Frontend workflow summary created
- [x] Project plan created
- [x] Todo tracking created

---

## Key Principles

1. **Example-Driven Development:** Work on `resources-basket-pages-example-report.html` until perfect, then replicate in pipeline

2. **Separation of Concerns:**
   - Sample data: `sample_data/basket_pages_example.json`
   - Visuals: CSS in `css/`
   - Templates: Jinja2 in `templates/`
   - Logic: Python in `src/utils/html_report_generator.py`

3. **Build Once, Deploy Everywhere:** Pipeline should produce exact same output as local development

---

## File Reference

| File | Purpose |
|------|---------|
| `css/` | Sass source files |
| `output/css/main.css` | Compiled CSS |
| `templates/` | Jinja2 templates |
| `scripts/build_css.py` | CSS build script |
| `scripts/regenerate_example_report.py` | Example report generator |
| `sample_data/basket_pages_example.json` | Reference data |
| `output/resources-basket-pages-example-report.html` | Reference report |
| `src/utils/html_report_generator.py` | Main report generator |
