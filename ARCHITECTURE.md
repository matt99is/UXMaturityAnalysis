# Architecture & Extensibility Guide

This document explains the architecture of the UX Analysis Agent and how to extend it for different use cases.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                   (Orchestrator)                             │
└───────────────┬─────────────────────────────────────────────┘
                │
                ├──────────────────────────────────────────────┐
                │                                              │
                ▼                                              ▼
    ┌─────────────────────┐                      ┌──────────────────────┐
    │  config_loader.py   │                      │   .env (API Keys)    │
    │  (Configuration)    │                      └──────────────────────┘
    └──────────┬──────────┘
               │ reads
               ▼
    ┌─────────────────────┐
    │    config.yaml      │
    │  (UX Criteria)      │
    └─────────────────────┘

    Analysis Pipeline:
    ┌──────────────────────────────────────────────────────────┐
    │  1. Screenshot Capture (screenshot_capture.py)           │
    │     ├─ Playwright browser automation                     │
    │     ├─ Multi-viewport capture (desktop/mobile)           │
    │     └─ Save to screenshots/                              │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │  2. AI Analysis (claude_analyzer.py)                     │
    │     ├─ Load screenshots as base64                        │
    │     ├─ Build dynamic prompt from config criteria         │
    │     ├─ Call Claude API with vision                       │
    │     └─ Parse structured JSON response                    │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────────────────┐
    │  3. Report Generation (report_generator.py)              │
    │     ├─ Generate JSON report → output/                    │
    │     └─ Generate Markdown report → output/                │
    └──────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Configuration System (`config_loader.py`)

**Purpose:** Load and validate analysis configurations from YAML.

**Key Classes:**
- `AnalysisConfig`: Main config manager
- `AnalysisType`: Represents an analysis type (basket pages, product pages, etc.)
- `EvaluationCriterion`: Individual UX criterion
- `ScreenshotConfig`: Screenshot capture settings

**Extensibility:**
```python
# Add new analysis types in config.yaml without code changes
config = AnalysisConfig()
analysis = config.get_analysis_type("your_new_type")
```

### 2. Screenshot Capture (`screenshot_capture.py`)

**Purpose:** Automated browser control and screenshot capture.

**Key Classes:**
- `ScreenshotCapture`: Main capture class
  - `capture_url()`: Capture single URL
  - `capture_multiple_viewports()`: Multi-device capture
- `JourneyCapture`: (Future) Multi-step navigation

**Extension Points:**
```python
# Current: Single URL
result = await capturer.capture_url(url, site_name)

# Future: Multi-step journey
journey = JourneyCapture()
await journey.execute_journey([
    {"action": "navigate", "url": "..."},
    {"action": "click", "selector": ".product"},
    {"action": "screenshot", "name": "product_page"}
])
```

### 3. Claude Analysis (`claude_analyzer.py`)

**Purpose:** AI-powered UX analysis using Claude's vision capabilities.

**Key Classes:**
- `ClaudeUXAnalyzer`: Main analyzer
  - `analyze_screenshots()`: Analyze with criteria
  - `_build_analysis_prompt()`: Dynamic prompt generation
- `ComparativeAnalyzer`: (Future) Multi-competitor comparison

**Extension Points:**
```python
# Works with any criteria from config
analyzer = ClaudeUXAnalyzer(api_key)
result = await analyzer.analyze_screenshots(
    screenshot_paths=paths,
    criteria=your_custom_criteria,  # From config.yaml
    analysis_name="Your Analysis Type"
)
```

### 4. Report Generation (`report_generator.py`)

**Purpose:** Generate structured reports in multiple formats.

**Key Classes:**
- `ReportGenerator`: JSON and Markdown reports
- `HTMLReportGenerator`: (Future) Interactive HTML reports

**Extension Points:**
```python
# Add new report formats
class CustomReportGenerator(ReportGenerator):
    def generate_pdf_report(self, results):
        # Your implementation
        pass
```

## Extension Patterns

### Pattern 1: Adding New Analysis Types

**No code changes required!** Just update `config.yaml`:

```yaml
analysis_types:
  checkout_pages:
    name: "Checkout Flow Analysis"
    description: "UX analysis of checkout pages"
    navigation:
      target_url: "direct"
    screenshot_config:
      viewports:
        - name: "desktop"
          width: 1920
          height: 1080
      full_page: true
    criteria:
      - id: "form_design"
        name: "Form Field Design"
        weight: 10
        description: "Quality of form fields and layout"
        evaluation_points:
          - "Are form fields clearly labeled?"
          - "Is autofill supported?"
        benchmarks:
          - "Baymard: Good form design reduces abandonment"
```

Run with:
```bash
python main.py --analysis-type checkout_pages --urls https://example.com/checkout
```

### Pattern 2: Multi-Step Journeys (Future)

The architecture supports multi-step journeys:

```yaml
# In config.yaml
navigation:
  steps:
    - action: "navigate"
      url: "{base_url}"
    - action: "click"
      selector: ".product-link"
      wait: 2000
    - action: "click"
      selector: ".add-to-basket"
    - action: "navigate"
      url: "{base_url}/basket"
```

Implementation in `JourneyCapture` class (currently placeholder).

### Pattern 3: Custom Prompts

Prompts are built dynamically from criteria:

```python
# In claude_analyzer.py
def _build_analysis_prompt(self, criteria, analysis_name, ...):
    # Template-based approach
    # Criteria are injected from config
    # Easy to customize per analysis type
```

### Pattern 4: Custom Output Formats

Extend `ReportGenerator`:

```python
from src.utils.report_generator import ReportGenerator

class PDFReportGenerator(ReportGenerator):
    def generate_pdf_report(self, analysis_results):
        # Use reportlab, weasyprint, etc.
        pass
```

## Data Flow

### Input
```
Competitor URLs → Config (criteria) → Environment (API keys)
```

### Processing
```
1. URLs → Playwright → Screenshots (PNG files)
2. Screenshots + Criteria → Claude API → Structured Analysis (JSON)
3. Analysis Results → Report Generator → Reports
```

### Output
```
output/
  ├── ux_analysis_TIMESTAMP.json        # Structured data
  └── ux_analysis_report_TIMESTAMP.md   # Human-readable

screenshots/
  ├── competitor_desktop_TIMESTAMP.png
  └── competitor_mobile_TIMESTAMP.png
```

## Configuration Schema

### Analysis Type Structure

```python
{
  "name": str,                    # Display name
  "description": str,             # Purpose
  "navigation": {
    "target_url": "direct",       # Or multi-step config
    "fallback_strategy": str
  },
  "screenshot_config": {
    "viewports": [...],           # Desktop, mobile, tablet
    "full_page": bool,
    "capture_states": [...]       # initial, filled, etc.
  },
  "criteria": [                   # List of evaluation criteria
    {
      "id": str,
      "name": str,
      "weight": int,              # 1-10
      "description": str,
      "evaluation_points": [...],
      "benchmarks": [...]
    }
  ],
  "output_template": {...}        # Report structure
}
```

## Extending to New Page Types

### Example: Product Page Analysis

1. **Define Criteria** (`config.yaml`):
```yaml
analysis_types:
  product_pages:
    name: "Product Page Analysis"
    criteria:
      - id: "product_imagery"
        name: "Product Image Quality"
        weight: 9
        evaluation_points:
          - "Are images high quality and zoomable?"
          - "Multiple angles available?"
      - id: "product_description"
        name: "Product Description"
        weight: 8
        # ... more criteria
```

2. **Run Analysis**:
```bash
python main.py --analysis-type product_pages \
  --urls https://shop.com/product/123
```

No code changes needed!

## Testing & Validation

### Configuration Validation
```bash
python test_config.py
```

### Setup Verification
```bash
python verify_setup.py
```

### Full Analysis Test
```bash
# Create test competitors file
python main.py --config test_competitors.json
```

## Performance Considerations

### Current Implementation
- **Sequential**: Analyzes one competitor at a time
- **Time per competitor**: ~30-60 seconds
  - Screenshot: ~5-10 seconds
  - Claude API: ~20-40 seconds
  - Report generation: ~1-2 seconds

### Future Optimizations
```python
# Parallel analysis
import asyncio

async def analyze_all():
    tasks = [
        orchestrator.analyze_competitor(url1, name1),
        orchestrator.analyze_competitor(url2, name2),
        orchestrator.analyze_competitor(url3, name3)
    ]
    results = await asyncio.gather(*tasks)
```

Could reduce total time by ~3x for multiple competitors.

## Error Handling

The system handles:
- **Screenshot failures**: Continues with other viewports
- **API errors**: Returns error in results, continues with next competitor
- **Invalid URLs**: Catches and reports
- **Missing config**: Validation at startup

Results always include `success: true/false` flag.

## Security Considerations

- API keys in `.env` (git-ignored)
- No credentials stored in code
- Screenshots may contain PII - handle accordingly
- Rate limiting on Claude API (managed by SDK)

## Future Enhancements

### Planned Architecture Changes

1. **Database Integration**
   - Store historical analyses
   - Track changes over time
   - Query and compare

2. **Plugin System**
   - Custom analyzers
   - Custom report formats
   - Custom capture strategies

3. **Web Interface**
   - Upload URLs via web form
   - View reports in browser
   - Schedule recurring analyses

4. **Integration APIs**
   - Export to GA4
   - ContentSquare integration
   - Slack/email notifications

## Best Practices

1. **Configuration over Code**: Add new analyses via config.yaml
2. **Fail Gracefully**: Handle errors without stopping entire pipeline
3. **Structured Output**: Always return structured data for programmatic use
4. **Extensibility Markers**: Look for "EXTENSIBILITY NOTE" comments in code
5. **Version Control**: Track config.yaml changes to see criteria evolution

---

**For implementation examples, see the code files themselves - all key extension points are marked with "EXTENSIBILITY NOTE" comments.**
