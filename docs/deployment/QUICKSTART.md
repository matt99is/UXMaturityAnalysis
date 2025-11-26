# 🚀 Quick Deploy to Netlify

## Fastest Way (30 seconds)

1. **Generate index page:**
   ```bash
   python3 scripts/generate_index.py
   ```

2. **Open Netlify Drop:**
   - Go to **https://app.netlify.com/drop**

3. **Drag & Drop:**
   - Drag your `output/audits` folder onto the page

4. **Done!** You'll get a URL like:
   ```
   https://competitor-reports-abc123.netlify.app
   ```

Share this URL with anyone - they can view all your reports!

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

# 2. Update index page
python3 scripts/generate_index.py

# 3. Re-deploy
# Go to https://app.netlify.com/drop
# Drag output/audits folder again
```

---

## For More Options

See **NETLIFY_DEPLOY.md** for:
- CLI deployment (automated)
- GitHub auto-deploy (push to deploy)
- Password protection
- Custom domains

---

**That's it!** You now have professional, shareable competitive intelligence reports. 🎉
