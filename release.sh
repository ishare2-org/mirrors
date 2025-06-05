#!/bin/bash

set -e

# === CONFIG ===
TAG_PREFIX="LabHub-Index"
RELEASE_PREFIX="LabHub-Indexes"
DIST_DIR="./dist"
VERSION="$1"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

TAG_NAME="${TAG_PREFIX}-${VERSION}"
RELEASE_NAME="${RELEASE_PREFIX}-${VERSION}"
RELEASE_TITLE="LabHub Indexes ${VERSION}"
RELEASE_BODY="Automated release of index files for version ${VERSION}"

# === TAG AND PUSH ===
echo "Creating git tag: ${TAG_NAME}"
git tag "${TAG_NAME}"
git push origin "${TAG_NAME}"

# === CREATE RELEASE ===
echo "Creating GitHub release: ${RELEASE_NAME}"
gh release create "${RELEASE_NAME}" -t "${RELEASE_TITLE}" -n "${RELEASE_BODY}"

# === UPLOAD ASSETS ===
echo "Uploading JSON files from ${DIST_DIR}"
gh release upload "${RELEASE_NAME}" "${DIST_DIR}"/*.json

echo "✅ Release ${RELEASE_NAME} complete!"
