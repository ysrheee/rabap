#!/bin/bash
# 라밥 웹 배포: 빌드 번호 갱신 → 커밋 → 푸시
set -e
cd ~/rabap
BUILD=$(date +%Y%m%d%H%M%S)
sed -i '' -E "s/const BUILD = \"[^\"]*\";/const BUILD = \"$BUILD\";/" docs/index.html
echo "{\"build\":\"$BUILD\"}" > docs/version.json
git add -A
git commit -qm "${1:-deploy} [$BUILD]" || true
git push -q origin main
echo "deployed $BUILD"
