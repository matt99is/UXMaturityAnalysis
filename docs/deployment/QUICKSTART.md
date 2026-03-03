# Quick Deploy to Netlify

## Fastest Way (30 seconds)

1. **Generate reports:**
   ```bash
   ./run.sh    # choose "Fresh analysis"
   ```
   Reports are written to `output/` and `output/index.html` is auto-updated.

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

## After Each New Analysis

```bash
# 1. Run your analysis
./run.sh    # choose "Fresh analysis" — it auto-deploys on clean runs

# 2. Or manually re-deploy after reanalyse
./run.sh --deploy
```

---

## For More Options

See **NETLIFY.md** for:
- CLI deployment setup
- GitHub auto-deploy (push to deploy)
- Password protection
- Custom domains
