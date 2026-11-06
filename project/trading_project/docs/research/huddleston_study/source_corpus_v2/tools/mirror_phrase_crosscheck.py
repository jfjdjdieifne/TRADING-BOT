#!/usr/bin/env python3
"""Mechanical mirror cross-check.

Takes 10 evenly spaced word-windows (10 words each, within the requested 8-12
range) from the already-stored YouTube part_0 of a video and counts how many
appear verbatim in the concatenated mirror response text. Reports COUNTS ONLY.

Match modes reported:
  strict      : exact substring match, case sensitive, raw bytes-as-text
  normalized  : case-insensitive, all whitespace runs collapsed to one space
No text is altered on disk; this script only reads.
"""
import sys, re, pathlib

def body(p):
    t = pathlib.Path(p).read_text(encoding='utf-8')
    if '## Transcript' in t:
        t = t.split('## Transcript', 1)[1]
    return t

def norm(t):
    return re.sub(r'\s+', ' ', t).strip().lower()

def main():
    part0 = sys.argv[1]
    mirror_files = sys.argv[2:]
    src = body(part0)
    words = src.split()
    W = 10
    N = 10
    if len(words) < W * N:
        stride = max(1, (len(words) - W) // max(1, N - 1))
    else:
        stride = (len(words) - W) // (N - 1)
    phrases = [' '.join(words[i*stride:i*stride+W]) for i in range(N)]
    phrases = [p for p in phrases if len(p.split()) == W][:N]
    mirror_raw = '\n'.join(pathlib.Path(f).read_text(encoding='utf-8') for f in mirror_files)
    mirror_norm = norm(mirror_raw)
    strict = sum(1 for p in phrases if p in mirror_raw)
    normalized = sum(1 for p in phrases if norm(p) in mirror_norm)
    print(f'phrases_tested={len(phrases)}')
    print(f'verbatim_strict_matches={strict}')
    print(f'normalized_case_insensitive_matches={normalized}')

if __name__ == '__main__':
    main()
