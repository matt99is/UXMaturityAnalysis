# Bot Detection Handling Guide

**Version:** 1.1.0

This guide explains how to handle bot detection when analyzing competitors with strong anti-scraping protection.

---

## 🤖 The Bot Detection Problem

Many major e-commerce sites use sophisticated bot detection:
- **Amazon, eBay, Etsy**: DataDome, PerimeterX
- **Major retailers**: Cloudflare Bot Management
- **Enterprise sites**: Custom anti-bot solutions

These systems detect and block automated browsers like Playwright/Selenium.

---

## ✅ Solution: Three Modes

### 1. **Automated Mode** (Default)
**Best for:** Smaller sites, sites without bot detection

```bash
python main.py --urls https://site1.com https://site2.com
```

- Runs headless (fast)
- No user interaction needed
- Works for most sites

**When it fails:** You'll see "Access Denied", CAPTCHA, or blank screenshots

---

### 2. **Interactive Mode with Manual Assist** (Hybrid) ⭐ **Recommended**
**Best for:** Sites with moderate bot detection, checkout flows

**How it works:**
1. Tool opens visible browser
2. If bot detected, shows red alert with instructions
3. You manually navigate and solve CAPTCHAs
4. Press Enter when ready
5. Tool captures screenshots

```bash
# Checkout pages automatically use interactive mode
python main.py --analysis-type checkout_pages --urls https://site.com/checkout
```

**What you'll see when blocked:**
```
⚠ Bot Detection Triggered: Access Denied

🤖 BOT DETECTED - Manual Navigation Required:
1. The visible browser may show CAPTCHA or 'Access Denied'
2. Manually navigate to the correct page
3. Complete any CAPTCHAs or verification steps
4. Set up the page as needed (add items, navigate, etc.)
5. Press Enter below when page is ready

[Press Enter when ready to capture screenshots...]
```

---

### 3. **Manual Screenshot Mode** (Backup) ⭐ **For Heavy Bot Detection**
**Best for:** Amazon, eBay, sites requiring login, maximum control

**Step 1: Capture screenshots manually**
```bash
# Create a directory
mkdir my-screenshots

# Open browser normally, navigate to competitor pages
# Take screenshots:
# - competitor1_desktop.png (1920x1080)
# - competitor1_mobile.png (375x812)
```

**Step 2: Run analysis**
```bash
python main.py --manual-mode \
  --screenshots-dir ./my-screenshots \
  --urls https://competitor1.com
```

**Supported naming patterns:**
- `{competitor}_desktop.png` and `{competitor}_mobile.png`
- `desktop.png` and `mobile.png` (if only one competitor)
- `{competitor}-desktop.png` (hyphen variant)

---

## 📊 Decision Matrix

| Site Type | Bot Detection | Recommended Mode | Example |
|-----------|---------------|------------------|---------|
| Small e-commerce | None/Weak | Automated | `python main.py --urls https://site.com` |
| Medium retailer | Moderate | Interactive | Opens visible browser, manual assist if needed |
| Amazon, eBay | Strong | Manual Mode | `--manual-mode --screenshots-dir ./screenshots` |
| Requires login | N/A | Manual Mode | Can't automate auth |
| Checkout flow | Varies | Interactive | Already configured in checkout_pages.yaml |

---

## 💡 Tips & Best Practices

### For Automated Mode:
- ✅ Test with your own sites first
- ✅ Use for smaller competitors
- ✅ Good for bulk homepage analysis

### For Interactive Mode:
- ✅ Keep browser window visible
- ✅ Have CAPTCHA solver ready (hCaptcha, reCAPTCHA)
- ✅ Timeout is 5 minutes by default
- ✅ You can navigate freely - tool waits for Enter key

### For Manual Mode:
- ✅ Use consistent screenshot sizes:
  - Desktop: 1920x1080
  - Mobile: 375x812
- ✅ Capture full page if possible
- ✅ Save as PNG format
- ✅ Use clear naming (competitor name should match URL)
- ✅ Perfect for one-off competitive audits

---

## 🔧 Configuration

### Change Interactive Timeout
Edit `criteria_config/checkout_pages.yaml`:
```yaml
interaction_timeout: 600  # 10 minutes
```

### Disable Interactive Mode
Force automated for checkout pages (not recommended):
```yaml
requires_interaction: false
```

---

## 📝 Examples

### Example 1: Mixed Approach
```bash
# Most sites work automated, one blocked
python main.py --urls https://good1.com https://good2.com

# Manually capture blocked site separately
python main.py --manual-mode \
  --screenshots-dir ./amazon-screenshots \
  --urls https://amazon.com
```

### Example 2: All Manual
```bash
# Capture all screenshots manually (in Chrome/Firefox)
# amazon_desktop.png, amazon_mobile.png
# ebay_desktop.png, ebay_mobile.png

python main.py --manual-mode \
  --screenshots-dir ./all-screenshots \
  --urls https://amazon.com https://ebay.com
```

### Example 3: Interactive Checkout
```bash
# Tool opens browser, you add items to cart
python main.py --analysis-type checkout_pages \
  --urls https://competitor.com/checkout

# You'll see:
# 1. Browser opens
# 2. Navigate and add items
# 3. Press Enter
# 4. Screenshots captured
```

---

## ⚠️ Ethical Considerations

### ✅ Acceptable Use:
- Analyzing public pages
- Competitive UX research
- One-off audits
- Respecting robots.txt

### ❌ Not Acceptable:
- Circumventing bot detection at scale
- Price scraping operations
- Automated data harvesting
- Violating terms of service

**Recommendation:** Use manual mode for heavily protected sites. You're the human, so no ethical issues!

---

## 🐛 Troubleshooting

### "All screenshot captures failed"
- **Automated mode**: Site is blocking bot → Use interactive or manual mode
- **Interactive mode**: Check if you navigated to correct page before pressing Enter
- **Manual mode**: Check screenshot files exist and naming matches

### "Screenshots are blank/error page"
- Bot detected in automated mode → Switch to manual mode
- Check console for "Bot detection: Access Denied" warning

### "Cannot find screenshot files"
- Check `--screenshots-dir` path is correct
- Verify file naming: `{competitor}_desktop.png`
- Use `ls` to confirm files exist

### Browser doesn't open (Interactive mode)
- Check Playwright is installed: `playwright install chromium`
- Verify not running in headless-only environment
- Check display is available (not SSH session)

---

## 📚 Related Documentation

- [README.md](../README.md) - Main documentation
- [CHANGELOG.md](../CHANGELOG.md) - Version 1.1.0 release notes
- [SAMPLE_OUTPUT.md](./SAMPLE_OUTPUT.md) - Example reports

---

**Version:** 1.1.0
**Last Updated:** 2025-11-20
