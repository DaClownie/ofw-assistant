#!/bin/bash

echo "================================================"
echo "OFW Assistant Release Builder"
echo "================================================"
echo ""

# Step 1: Version management
echo "Step 1: Updating version and changelog..."
python3 version_manager.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Version update cancelled."
    echo ""
    read -p "Create installer anyway without version bump? (y/n): " continue_anyway
    
    if [ "$continue_anyway" != "y" ]; then
        echo "Exiting."
        exit 0
    fi
fi

echo ""
echo "Step 2: Creating installer package..."
python3 create_installer.py

if [ $? -ne 0 ]; then
    echo "Installer creation failed. Exiting."
    exit 1
fi

echo ""
echo "Step 3: Creating distribution package..."
python3 package_for_distribution.py

if [ $? -ne 0 ]; then
    echo "Distribution package creation failed. Exiting."
    exit 1
fi

echo ""
echo "================================================"
echo "Release complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Test the DMG file"
echo "2. Commit version.json and CHANGELOG.md to git"
echo "3. Distribute the DMG file"