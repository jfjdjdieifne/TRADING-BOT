# extraction - corpus tooling

One job: get the source material onto disk and index it. **Three scripts, all
free, none needing a key.**

| script | does |
|---|---|
| `fetch_transcripts.py` | pulls YouTube caption tracks for the playlist into `../transcripts/`. Resumable |
| `build_index.py` | regenerates `../corpus/_index.md` from what exists on disk |
| `build_refinements.py` | builds `../study/_refinements.md` - the cross-episode concept index and all 144 revision notes. **Read it before implementing any rule** |
| `backup.py` | verified zip into `../_backups/`. This was the only history on the machine before git |

## What used to be here, and why it is gone

An automated extraction pass ran here for three days: Gemini over sampled video
frames, then over transcript chunks, producing structured claims into
`extraction/output/` and grouped concept pages into `../bundle/`.

**It was overtaken and removed on 2026-09-04.** The hand-written `../study/`
pages cover all 40 available episodes; the automated pass reached ten. Nothing
downstream depended on it, and its remaining value was noise in a finished
repository.

**The reasoning survives in `../DECISIONS.md`** - and it is the part worth
keeping. Section 19 measured video against transcript instead of arguing about
it; section 1 records how provenance stopped being trusted and started being
checked by script; sections 10, 12, 13, 14 and 15 carry the extraction rulings.
Section 25 records this deletion.

**The API key went with it.** No script here reads a credential.
