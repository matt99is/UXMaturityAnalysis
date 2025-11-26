# Netlify Deployment Guide

Deploy your competitive intelligence reports to Netlify for easy sharing via URL.

## Why Netlify?

✅ **100% Free** for your use case
✅ **No file size limits** to worry about
✅ **Shareable links** - just send the URL
✅ **Password protection** available (even on free tier)
✅ **Automatic HTTPS**
✅ **Fast global CDN**

---

## Quick Start (3 Options)

### Option 1: Drag & Drop (Easiest - 30 seconds)

1. Generate the index page:
   ```bash
   python3 scripts/generate_index.py
   ```

2. Go to **https://app.netlify.com/drop**

3. Drag the `output/audits` folder onto the page

4. **Done!** Get your shareable link like:
   ```
   https://your-reports-abc123.netlify.app
   ```

**That's it!** Share the link with anyone.

---

### Option 2: CLI Deployment (Recommended for repeat deployments)

#### First Time Setup (5 minutes)

1. Install Netlify CLI:
   ```bash
   npm install -g netlify-cli
   ```

2. Login to Netlify:
   ```bash
   netlify login
   ```
   (Opens browser to authorise)

3. Initialize your site:
   ```bash
   cd output/audits
   netlify init
   ```

   Select:
   - "Create & configure a new site"
   - Choose team (personal)
   - Choose site name (e.g., "competitor-analysis")

4. Deploy:
   ```bash
   python3 scripts/deploy_netlify.py
   ```

#### Future Deployments (10 seconds)

After initial setup, just run:

```bash
python3 scripts/deploy_netlify.py
```

The script will:
- ✓ Generate index.html with all reports
- ✓ Deploy to Netlify
- ✓ Give you the live URL

---

### Option 3: GitHub + Netlify (Auto-deploy)

#### Setup (One-time, 10 minutes)

1. Create a GitHub repo for reports:
   ```bash
   cd output/audits
   git init
   git add .
   git commit -m "Initial reports"
   gh repo create competitive-reports --public --push
   ```
   (Or create repo manually at github.com)

2. Connect to Netlify:
   - Go to **https://app.netlify.com**
   - Click "Add new site" → "Import an existing project"
   - Choose GitHub → Select your `competitive-reports` repo
   - Configure:
     - Build command: `echo "Static site"`
     - Publish directory: `.` (root)
   - Click "Deploy site"

3. **Done!** Every git push auto-deploys.

#### Future Workflow

```bash
# After generating new reports
python3 scripts/generate_index.py  # Update index
cd output/audits
git add .
git commit -m "New basket analysis Dec 2024"
git push

# Automatically deploys to Netlify!
```

---

## Features

### 📊 Report Dashboard

The auto-generated `index.html` provides:
- List of all reports with dates
- Analysis type (Basket Pages, Product Pages, etc.)
- Competitor count
- One-click access to each report

### 🔒 Password Protection (Optional)

**Free tier supports password protection!**

1. Go to your site settings in Netlify dashboard
2. Navigate to "Site settings" → "Access control"
3. Enable "Password protection"
4. Set a password
5. Share URL + password with authorised users

### 🎨 Custom Domain (Optional)

**Free custom domains on free tier:**

1. In Netlify dashboard: "Domain management" → "Add custom domain"
2. Add your domain (e.g., `reports.yourcompany.com`)
3. Update DNS records as instructed
4. Automatic HTTPS included!

---

## File Structure

After deployment, your site will have:

```
https://your-site.netlify.app/
├── index.html                           ← Report dashboard (homepage)
├── 2025-11-24_basket_pages/
│   ├── 2025-11-24_basket_pages_report.html  ← Interactive report
│   ├── _comparison_report.md
│   ├── zooplus/
│   │   └── screenshots/
│   │       ├── desktop.png
│   │       └── mobile.png
│   └── morrisons/
│       └── screenshots/
└── 2025-11-21_product_pages/
    └── ...
```

**URLs:**
- Homepage: `https://your-site.netlify.app/`
- Basket report: `https://your-site.netlify.app/2025-11-24_basket_pages/2025-11-24_basket_pages_report.html`
- Product report: `https://your-site.netlify.app/2025-11-21_product_pages/...`

---

## Updating Reports

### After running a new analysis:

```bash
# 1. Generate new report
python main.py --urls ...

# 2. Update index
python3 scripts/generate_index.py

# 3. Deploy (choose one):

# Option A: Drag & drop (manual)
# - Go to https://app.netlify.com/drop
# - Drag output/audits folder

# Option B: CLI (automated)
python3 scripts/deploy_netlify.py

# Option C: Git (auto-deploy)
cd output/audits
git add .
git commit -m "New analysis"
git push  # Auto-deploys!
```

---

## Cost Breakdown

### Netlify Free Tier (Forever Free)

**Included:**
- ✅ 100 GB bandwidth/month
- ✅ 300 build minutes/month
- ✅ Unlimited sites
- ✅ HTTPS
- ✅ Password protection
- ✅ Custom domains

**What 100 GB bandwidth means:**
- Each full report view = ~1-2 MB (HTML + screenshots)
- 100 GB = ~50,000 - 100,000 report views per month
- Unless you're sharing with thousands of people, you'll never hit this limit

**If you exceed limits:**
- Paid plan: $19/month (unlimited bandwidth)
- But realistically, you won't need it

### Zero Cost Setup

If you choose **drag & drop** or **CLI with manual deploy**, there are:
- ❌ No recurring costs
- ❌ No credit card required
- ❌ No surprises

---

## Troubleshooting

### "Site not linked" error

```bash
cd output/audits
netlify init
```

Then retry deployment.

### Large files warning

If you get file size warnings:
- This is expected for screenshots
- Netlify supports large files (up to 50 MB per file)
- Your total site can be several GB

### Images not loading

Check that `output/audits` contains:
- All report HTML files
- All `*/screenshots/*.png` files
- The generated `index.html`

Run `tree output/audits -L 3` to verify structure.

---

## Security Notes

### Public Deployment

- By default, anyone with the URL can view reports
- Consider password protection for sensitive data

### Private Repositories

- If using GitHub integration, you can use private repos
- Reports still deploy to public Netlify URL
- Use password protection for access control

### Data Considerations

- Netlify servers are in US (check compliance requirements)
- GDPR: Netlify is GDPR compliant
- CCPA: Netlify is CCPA compliant

---

## Next Steps

1. **Test locally** (optional):
   ```bash
   cd output/audits
   python3 -m http.server 8000
   # Visit: http://localhost:8000
   ```

2. **Deploy**:
   - Choose your deployment method above
   - Share the URL!

3. **Automate** (optional):
   - Add `python3 scripts/generate_index.py` to your workflow
   - Or connect GitHub for auto-deployment

---

## Support

**Netlify Documentation:**
- https://docs.netlify.com/

**Netlify CLI Help:**
```bash
netlify help
netlify deploy --help
```

**Questions?**
- Netlify Community: https://answers.netlify.com/
