#!/bin/bash
# /tmp is wiped between calls in this sandbox: fetch the pinned corpus into /tmp/dr if absent.
set -e
T=/tmp/dr/newsqlguru__ict-index
if [ ! -d "$T" ] || [ "$(find "$T" -name '*.json' | wc -l)" -lt 490 ]; then
  mkdir -p "$T"
  curl -sSL https://codeload.github.com/newsqlguru/ict-index/tar.gz/e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c \
    | tar -xz -C "$T" --strip-components=1
  echo "corpus_fetched=$(find "$T" -name '*.json' | wc -l)"
else
  echo "corpus_present=$(find "$T" -name '*.json' | wc -l)"
fi
