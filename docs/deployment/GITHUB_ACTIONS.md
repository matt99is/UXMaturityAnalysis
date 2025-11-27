# GitHub Actions Auto-Deployment

Automatically deploy your reports to Netlify whenever you push changes to the `output/audits` directory.

## Why GitHub Actions?

✅ **Fully Automatic** - deploys on every push
✅ **Works with Private Repos** - unlike Netlify's native GitHub integration
✅ **Free** - GitHub Actions is free for public and private repos
✅ **No Manual Steps** - set it up once, forget about it
✅ **Selective Deployment** - only triggers when reports change

---

## One-Time Setup (5 minutes)

### Step 1: Get Your Netlify Credentials

#### 1a. Get Netlify Auth Token

1. Go to **https://app.netlify.com/user/applications**
2. Scroll to "Personal access tokens"
3. Click **"New access token"**
4. Name it: `GitHub Actions Deploy`
5. Click **"Generate token"**
6. **Copy the token** (you won't see it again!)

#### 1b. Get Netlify Site ID

**Option A: From existing site**
1. Go to https://app.netlify.com
2. Open your site
3. Go to **Site settings > General > Site details**
4. Copy the **Site ID** (looks like: `abc12345-6789-def0-1234-56789abcdef0`)

**Option B: Create new site first**
1. Go to https://app.netlify.com/drop
2. Drag the `output/audits` folder to create a site
3. Once created, follow "Option A" above to get the Site ID

---

### Step 2: Add Secrets to GitHub

1. Go to your GitHub repo: **https://github.com/matt99is/UXMaturityAnalysis**

2. Click **Settings** (top menu)

3. In the left sidebar, click **Secrets and variables > Actions**

4. Click **"New repository secret"** and add:

   **Secret 1:**
   - Name: `NETLIFY_AUTH_TOKEN`
   - Value: [Paste your Netlify auth token from Step 1a]
   - Click **"Add secret"**

   **Secret 2:**
   - Name: `NETLIFY_SITE_ID`
   - Value: [Paste your Netlify site ID from Step 1b]
   - Click **"Add secret"**

---

### Step 3: Commit the Workflow

The workflow file is already created at `.github/workflows/deploy-netlify.yml`.

Just commit and push it:

```bash
git add .github/workflows/deploy-netlify.yml
git commit -m "Add GitHub Actions auto-deployment to Netlify"
git push
```

---

## How It Works

The workflow automatically runs when:
- ✅ You push changes to the `main` branch
- ✅ Files in `output/audits/` have changed
- ✅ Or you manually trigger it from GitHub Actions tab

### Workflow Steps:
1. Checks out your repository
2. Installs Netlify CLI
3. Deploys `output/audits` directory to your Netlify site
4. Shows deployment confirmation

---

## Testing the Deployment

### Option 1: Push a Report Change
```bash
# Generate/update a report
python3 main.py --config competitors.json

# Commit and push
git add output/audits/
git commit -m "Update reports"
git push
```

The deployment will trigger automatically!

### Option 2: Manual Trigger
1. Go to your GitHub repo
2. Click **Actions** tab
3. Click **"Deploy Reports to Netlify"** workflow
4. Click **"Run workflow"** button
5. Select `main` branch
6. Click **"Run workflow"**

---

## Monitoring Deployments

### View Deployment Status

1. Go to your GitHub repo
2. Click **Actions** tab
3. See all deployment runs with status (✅ success, ❌ failed)
4. Click any run to see detailed logs

### View Live Site

After successful deployment, visit:
```
https://[your-site-name].netlify.app
```

Or check your Netlify dashboard at https://app.netlify.com

---

## Troubleshooting

### ❌ Workflow fails with "Unauthorized"
- Check that `NETLIFY_AUTH_TOKEN` secret is set correctly
- Generate a new token if needed

### ❌ Workflow fails with "Site not found"
- Check that `NETLIFY_SITE_ID` secret matches your Netlify site ID
- Verify the site exists in your Netlify dashboard

### ❌ Workflow doesn't trigger
- Ensure you pushed changes to files inside `output/audits/`
- Check the Actions tab for any error messages
- Verify the workflow file is in `.github/workflows/` directory

### 🔍 Enable detailed logging
Edit `.github/workflows/deploy-netlify.yml` and add:
```yaml
env:
  DEBUG: '*'
```

---

## Customization

### Change Trigger Conditions

Edit `.github/workflows/deploy-netlify.yml`:

```yaml
# Deploy on any push to main
on:
  push:
    branches:
      - main

# Deploy only on specific files
on:
  push:
    branches:
      - main
    paths:
      - 'output/audits/**'
      - 'scripts/generate_index.py'
```

### Deploy to Different Directory

Change the deploy step:
```yaml
run: |
  netlify deploy \
    --dir=path/to/your/directory \
    --prod \
    ...
```

---

## Cost

**GitHub Actions:** Free
- 2,000 minutes/month for private repos
- Unlimited for public repos
- Each deployment takes ~1-2 minutes

**Netlify:** Free
- 100 GB bandwidth/month
- Unlimited sites
- 300 build minutes/month (not used with this setup)

You're well within free tier limits! 🎉
