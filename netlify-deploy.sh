#!/bin/bash
# Netlify deployment script for static HTML reports
# No dependencies needed - we deploy pre-generated files

echo "Deploying pre-generated static HTML reports from output/audits/"
echo "No build or dependency installation required."
ls -la output/audits/ || echo "Note: output/audits directory will be published"
