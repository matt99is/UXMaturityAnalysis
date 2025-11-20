# 🚀 Get Started with the UX Analysis Agent

## Welcome!

Your competitive UX analysis agent is ready to use. This guide will get you up and running in 5 minutes.

## 📋 What You Have

A complete, production-ready tool that:
- ✅ Captures screenshots of competitor basket pages
- ✅ Analyzes UX using Claude AI against 10 research-backed criteria
- ✅ Generates JSON and Markdown reports with actionable recommendations
- ✅ Supports extensibility for other page types

## ⚡ Quick Start (5 minutes)

### Step 1: Install Dependencies (2 min)

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### Step 2: Configure API Key (1 min)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Anthropic API key
# Get your key from: https://console.anthropic.com/
```

Edit `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 3: Verify Setup (30 sec)

```bash
python verify_setup.py
```

### Step 4: Run Your First Analysis (2 min)

```bash
# Example with two competitors
python main.py --urls \
  https://www.asos.com/bag \
  https://www.zara.com/cart
```

## 📊 What Happens Next

The tool will:
1. **Capture screenshots** (desktop & mobile) - ~10 seconds per competitor
2. **Analyze with Claude AI** - ~30 seconds per competitor
3. **Generate reports** in `output/` directory

## 📁 Find Your Results

After analysis completes:

```
output/
├── ux_analysis_20250115_103000.json      # Structured data
└── ux_analysis_report_20250115_103000.md # Human-readable report

screenshots/
├── competitor1_desktop_20250115_103000.png
├── competitor1_mobile_20250115_103005.png
├── competitor2_desktop_20250115_103100.png
└── competitor2_mobile_20250115_103105.png
```

## 📖 Essential Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **QUICKSTART.md** | Quick setup & usage | Start here |
| **README.md** | Complete documentation | For comprehensive guide |
| **ARCHITECTURE.md** | Technical details & extensibility | When extending the tool |
| **PROJECT_SUMMARY.md** | Project overview | For high-level understanding |

## 🎯 Common Use Cases

### Use Case 1: Analyze Specific Competitors

```bash
python main.py --urls \
  https://competitor1.com/basket \
  https://competitor2.com/cart \
  https://competitor3.com/shopping-bag
```

### Use Case 2: Use Configuration File

Create `my_competitors.json`:
```json
{
  "competitors": [
    {"name": "competitor1", "url": "https://competitor1.com/basket"},
    {"name": "competitor2", "url": "https://competitor2.com/cart"}
  ]
}
```

Run:
```bash
python main.py --config my_competitors.json
```

### Use Case 3: Customize Analysis Criteria

Edit `config.yaml` to:
- Add new evaluation criteria
- Change criterion weights
- Update benchmarks
- Modify evaluation points

No code changes needed!

## 🔧 Customization Quick Tips

### Change Viewports

Edit `config.yaml`:
```yaml
screenshot_config:
  viewports:
    - name: "desktop"
      width: 1920
      height: 1080
    - name: "tablet"
      width: 768
      height: 1024
    - name: "mobile"
      width: 375
      height: 812
```

### Add New Criteria

Edit `config.yaml`:
```yaml
criteria:
  - id: "your_new_criterion"
    name: "Your Criterion Name"
    weight: 8
    description: "What you're evaluating"
    evaluation_points:
      - "Question 1?"
      - "Question 2?"
    benchmarks:
      - "Benchmark from research"
```

## ❓ Troubleshooting

### "ANTHROPIC_API_KEY not found"
→ Create `.env` file and add your API key

### "playwright not found"
→ Run: `playwright install chromium`

### Screenshots are blank
→ URL might redirect or require login - verify URL is publicly accessible

### Analysis is slow
→ Normal! Each competitor takes ~30-60 seconds (screenshot + AI analysis)

## 📚 Learn More

- **Examples**: See `example_usage.py` for programmatic usage
- **Sample Output**: Check `output/sample_ux_analysis_report.md`
- **Verification**: Run `python test_config.py` to test config
- **Architecture**: Read `ARCHITECTURE.md` for extension patterns

## 🎓 What to Analyze

The tool evaluates 10 UX criteria:

1. **Shipping Cost Transparency** (Critical - #1 abandonment reason)
2. **Discount Code Field** (High confusion factor)
3. **Basket Summary Clarity** (Cost breakdown)
4. **Express Checkout** (Friction reduction)
5. **Delivery Estimates** (Cutoff times)
6. **CTA Buttons** (Copy & prominence)
7. **Mobile Responsiveness** (Mobile UX)
8. **Payment Methods** (Early visibility)
9. **Trust Signals** (Security & returns)
10. **Basket Saving** (Save for later)

All based on Baymard Institute and Nielsen Norman Group research.

## 🚀 Next Steps

1. ✅ Install dependencies
2. ✅ Add API key to `.env`
3. ✅ Run `verify_setup.py`
4. ✅ Analyze your first competitors
5. ✅ Review the reports
6. ✅ Customize criteria for your needs
7. ✅ Share insights with your team

## 💡 Pro Tips

1. **Start Small**: Test with 1-2 competitors first
2. **Check URLs**: Ensure basket pages are publicly accessible
3. **Review Criteria**: Customize `config.yaml` for your industry
4. **Save Reports**: Keep historical data to track competitor changes
5. **Iterate**: Use findings to refine your analysis criteria

## 🎉 You're Ready!

Run your first analysis:

```bash
python main.py --urls https://your-competitor.com/basket
```

---

**Questions?** Check the documentation files or review code comments marked "EXTENSIBILITY NOTE"

**Happy Analyzing! 🎯**
