#!/bin/bash
# Cleanup script to remove web interface files and prepare for publishing

echo "🧹 Cleaning up web interface files..."

# Remove web interface files
if [ -f "app.py" ]; then
    rm -f app.py
    echo "✅ Removed app.py"
fi

if [ -f "run.sh" ]; then
    rm -f run.sh
    echo "✅ Removed run.sh"
fi

if [ -d "templates" ]; then
    rm -rf templates/
    echo "✅ Removed templates/"
fi

# Remove duplicate README
if [ -f "README-NATIVE.md" ]; then
    rm -f README-NATIVE.md
    echo "✅ Removed README-NATIVE.md (merged into README.md)"
fi

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "✅ Removed __pycache__ directories"

# Remove cleanup files
rm -f FILES-TO-DELETE.txt
rm -f cleanup.sh
echo "✅ Removed temporary files"

echo ""
echo "✨ Cleanup complete!"
echo ""
echo "📦 Your project is now ready for publishing!"
echo ""
echo "Next steps:"
echo "1. Review PUBLISHING-CHECKLIST.md"
echo "2. Update personal information in setup.py, PKGBUILD, and LICENSE"
echo "3. Create GitHub repository and push code"
echo "4. Follow the AUR submission guide"
echo ""
