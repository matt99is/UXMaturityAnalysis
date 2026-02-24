# 🚀 Quick Deploy to Netlify

## Fastest Way (30 seconds)

1. **Generate reports** (this also updates `output/index.html` automatically):
   ```bash
   python3 main.py --config competitors.json --analysis-type product_pages
   ```

2. **Open Netlify Drop:**
   - Go to **https://app.netlify.com/drop**

3. **Drag & Drop:**
   - Drag your `output` folder onto the page

4. **Done!** You'll get a URL like:
   ```
   https://competitor-reports-abc123.netlify.app
   ```

Share this URL with anyone - they can browse all reports from the index homepage.

---

## What You Get

- ✅ **Report Dashboard** - Lists all your analyses
- ✅ **Shareable Links** - Send URL to clients/team
- ✅ **100% Free** - No credit card needed
- ✅ **Password Protection** - Available on free tier
- ✅ **Always Up-to-Date** - Redeploy anytime

---

## After Each New Analysis

```bash
# 1. Run your analysis
python main.py --urls https://example.com/basket

# 2. Re-deploy
# Go to https://app.netlify.com/drop
# Drag output folder again
```

---

## For More Options

See **NETLIFY.md** for:
- CLI deployment (automated)
- GitHub auto-deploy (push to deploy)
- Password protection
- Custom domains

---

**That's it!** You now have professional, shareable UX maturity reports. 🎉
