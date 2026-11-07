#!/bin/bash
# /tmp may be wiped between calls in this sandbox: fetch the pinned corpus into /tmp/dr if absent and verify SHA-256.
set -e
T=/tmp/dr/newsqlguru__ict-index
EXPECTED_SHA="4213e692f7c978dab8fe5ba124d34d887f17316c89d27bb2a7406fd3776f769d"
if [ ! -d "$T" ] || [ "$(find "$T" -name '*.json' | wc -l)" -lt 490 ]; then
  mkdir -p "$T"
  curl -sSL https://codeload.github.com/newsqlguru/ict-index/tar.gz/e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c -o /tmp/ict-index.tar.gz
  ACTUAL_SHA=$(sha256sum /tmp/ict-index.tar.gz | awk '{print $1}')
  if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then
    echo "ERROR: tarball SHA-256 mismatch: $ACTUAL_SHA != $EXPECTED_SHA" >&2
    exit 1
  fi
  tar -xzf /tmp/ict-index.tar.gz -C "$T" --strip-components=1
  echo "corpus_fetched=$(find "$T" -name '*.json' | wc -l) sha256=$ACTUAL_SHA"
else
  echo "corpus_present=$(find "$T" -name '*.json' | wc -l)"
fi
