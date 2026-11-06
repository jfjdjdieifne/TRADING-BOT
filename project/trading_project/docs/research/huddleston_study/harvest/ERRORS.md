# ERRORS — every URL tried, with result (success bytes+sha256, or exact error)

Generated 2026-11-06. Section D (web) is appended as pages are attempted.

## A. Terminal reachability probes (exact outputs)

| URL | result |
|---|---|
| `https://github.com` | 200, 527225 bytes, 0.377 s |
| `https://api.github.com/rate_limit` | 200, 1917 bytes, 0.310 s |
| `https://pypi.org/simple/` | 200, 48178804 bytes, 0.293 s |
| `https://codeload.github.com` | 301, 0 bytes |
| `https://registry.npmjs.org` | 200, 2 bytes |
| `https://files.pythonhosted.org` | 404, 10 bytes |
| `https://en.wikipedia.org/wiki/Market_trends` | curl (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to en.wikipedia.org:443 |
| `https://www.babypips.com/learn/forex` | curl (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to www.babypips.com:443 |
| `https://www.innercircletrader.com/` | curl (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to www.innercircletrader.com:443 |
| `https://raw.githubusercontent.com` | curl (35) ... SSL_ERROR_SYSCALL in connection to raw.githubusercontent.com:443 |
| `https://objects.githubusercontent.com` | curl (35) ... SSL_ERROR_SYSCALL in connection to objects.githubusercontent.com:443 |
| `https://archive.org` | curl (35) ... SSL_ERROR_SYSCALL in connection to archive.org:443 |
| `https://web.archive.org` | curl (35) ... SSL_ERROR_SYSCALL in connection to web.archive.org:443 |
| `https://www.forexfactory.com` | curl (35) ... SSL_ERROR_SYSCALL ...:443 |
| `https://www.reddit.com` | curl (35) ... SSL_ERROR_SYSCALL ...:443 |
| `https://medium.com` | curl (35) ... SSL_ERROR_SYSCALL ...:443 |
| `https://www.google.com` | curl (35) ... SSL_ERROR_SYSCALL ...:443 |
| `https://duckduckgo.com` | curl (35) ... SSL_ERROR_SYSCALL ...:443 |
| `http://en.wikipedia.org/wiki/Market_trends` | curl (52) Empty reply from server, code 000 |

Python equivalent: `urllib.request.urlopen('https://en.wikipedia.org/wiki/Market_trends', timeout=10)` → `URLError <urlopen error TLS/SSL connection has been closed (EOF) (_ssl.c:992)>`.

## B. GitHub search API calls (raw JSON saved in `search/`)

| # | HTTP | total_count | items returned | query | saved file |
|---|---|---|---|---|---|
| 1 | 200 | 43 | 43 | `inner circle trader` | `search/01_inner_circle_trader.json` |
| 2 | 200 | 21 | 21 | `ict mentorship` | `search/02_ict_mentorship.json` |
| 3 | 200 | 71 | 71 | `huddleston` | `search/03_huddleston.json` |
| 4 | 200 | 208 | 100 | `ict notes` | `search/04_ict_notes.json` |
| 5 | 200 | 1 | 1 | `innercircletrader` | `search/05_innercircletrader.json` |
| 6 | 200 | 1 | 1 | `smart money concepts notes` | `search/06_smart_money_concepts_notes.json` |
| 7 | 200 | 4 | 4 | `ict transcript` | `search/07_ict_transcript.json` |
| 8 | 200 | 2 | 2 | `smc course notes` | `search/08_smc_course_notes.json` |
| 9 | 200 | 68 | 68 | `order block fair value gap` | `search/09_order_block_fair_value_gap.json` |
| 10 | 200 | 290 | 100 | `liquidity sweep` | `search/10_liquidity_sweep.json` |
| 11 | 200 | 26 | 26 | `ict killzone` | `search/11_ict_killzone.json` |
| 12 | 200 | 8 | 8 | `judas swing` | `search/12_judas_swing.json` |
| 13 | 200 | 336 | 100 | `turtle soup` | `search/13_turtle_soup.json` |
| 14 | 200 | 39 | 39 | `silver bullet ict` | `search/14_silver_bullet_ict.json` |
| 15 | 200 | 0 | 0 | `ote 62 79` | `search/15_ote_62_79.json` |
| 16 | 200 | 3 | 3 | `premium discount dealing range` | `search/16_premium_discount_dealing_range.json` |
| 17 | 200 | 0 | 0 | `market structure shift displacement` | `search/17_market_structure_shift_displacement.json` |
| 18 | 200 | 26 | 26 | `ict study notes` | `search/18_ict_study_notes.json` |
| 19 | 200 | 2 | 2 | `smc trading book` | `search/19_smc_trading_book.json` |
| 20 | 200 | 7 | 7 | `ict chart examples` | `search/20_ict_chart_examples.json` |
| 21 | 200 | 0 | 0 | `ict captions transcript` | `search/21_ict_captions_transcript.json` |
| 22 | 200 | 0 | 0 | `inner circle trader transcript` | `search/22_inner_circle_trader_transcript.json` |
| 23 | 200 | 0 | 0 | `2022 mentorship transcript` | `search/23_2022_mentorship_transcript.json` |
| 24 | 200 | 0 | 0 | `ict concepts markdown notes` | `search/24_ict_concepts_markdown_notes.json` |
| 25 | 200 | 1 | 1 | `ict glossary terms` | `search/25_ict_glossary_terms.json` |
| 26 | 200 | 2 | 2 | `smart money concepts documentation` | `search/26_smart_money_concepts_documentation.json` |
| 27 | 200 | 0 | 0 | `ict trading notes github` | `search/27_ict_trading_notes_github.json` |
| 28 | 200 | 2 | 2 | `inner circle trader wiki` | `search/28_inner_circle_trader_wiki.json` |
| 29 | 200 | 5 | 5 | `ict pd arrays` | `search/29_ict_pd_arrays.json` |
| 30 | 200 | 7 | 7 | `order block explanation` | `search/30_order_block_explanation.json` |

All 30 search calls returned HTTP 200. No search call failed. Rate limit before the run: 5000 core / 30 search per minute.

## C. Repository metadata, tree and tarball retrieval

For each repository: `GET /repos/{full_name}` (200), `GET /repos/{full_name}/commits/{default_branch}` (200, SHA pinned), `GET /repos/{full_name}/git/trees/{sha}?recursive=1` (200, saved as `github/_meta/<owner>__<repo>__tree.json`), then `curl https://codeload.github.com/{full_name}/tar.gz/{sha}` → HTTP 200, extracted, and every text file hashed.

| repository | pinned commit | licence (spdx / from file) | tarball bytes |
|---|---|---|---|
| SrsBlack/ict-knowledge-library | `9b089669e5d1` | None | 2487208 |
| newsqlguru/ict-index | `e8c40a8dae5e` | GPL-3.0 | 10548984 |
| Yousef-Diab/the-algorithm | `af2fbf3b1342` | None | 82250395 |
| Rouen007/ict-2022-study-room | `86987a3230b4` | None | 24709144 |
| SaiStyles/ICT-2022-study | `f9e3a4184304` | NOASSERTION | 273859 |
| Mehranrostamy/ICT-Mentorship-2016-Month-1 | `d2ad83997ab3` | None | 65677 |
| Eymargriffin/ICT-mentorship-PDFs | `9d9da16c6cb8` | None | 42299 |
| icthammer/ICT-Mese5-CoreContent | `99048f1f664f` | None | 960866 |
| alptheexplorer/ICT-2024-MENTORSHIP | `78b27fd160d3` | None | 41266 |
| n4yr13/ICT-Mentorship | `22679ec7334c` | None | 6378 |
| kishore2296/DrMatrix | `4f70d9f23485` | None | 345 |
| gitwithuli/ict-wiki-archive | `ec82917e1632` | None | 34982574 |
| pravinkumardatafreak/ICT-JOURNAL- | `5aa45866f382` | None | 78241 |
| cecehj/ICT-Learning-Hub | `8cd69acc2242` | NOASSERTION | 1661 |
| BaShAh-s/Bashah-Traders | `da54dae25cad` | None | 3552 |
| globalfxhunter-create/globalfxhunter.github.io | `25ee862df80f` | None | 6874295 |
| Artprentice/ICT_Contest | `4d5674fad148` | None | 526917 |
| brainstrme/ICT-Trading | `cfa34fcb8a41` | None | 1741 |
| Kyle2077/ict-2022-skill-bundle | `4260b8a23782` | None | 41574823 |
| Sagar4575/ICT-2024-Mentorship-AI-Skill | `63b20fd611c6` | MIT | 53499 |
| zakariab0/ozo | `0ba2eaa7e470` | None | 30535 |
| kwpark090288-pixel/ICT-AutoTrader | `81c9981451b1` | None | 1361091 |
| thino-dev/Optimus-Prime-ICT_EA | `8f2d85939b42` | None | 25674 |
| yuvrajsingh1097/ICT-Smart-Money-Trading-Bot | `f5757760a192` | None | 598102 |
| Sagar4575/Sessions-and-Killzones | `230fd35d6c43` | NOASSERTION | 175276 |
| clintbarron/MMM-Killzones | `0d9b57885f53` | Apache-2.0 | 5601 |
| yusin99/Tradingview-Indicator---Pivots-and-Killzones | `ea9647fcf203` | MIT | 7747 |
| joshyattridge/smart-money-concepts | `1b62fd6c41e1` | MIT | 8218173 |
| islero/ICT-NT | `14f02517f620` | MIT | 329477 |
| LesterCS/Decoding-Institutional-Order-Flow-in-Python-like-ICT | `cc352532df87` | MIT | 77186 |
| tickets2themoon/ICTFVG | `3585c280afbc` | GPL-3.0 | 18027 |
| yuksels2/ICT-FVG-Tool | `393625034382` | None | 2693 |
| hindsight-finance/Silver-Bullet-AM-Session | `9f00a853288d` | None | 26869843 |
| martin254/Asian-Turtle-Soup-Trading-Bot | `4c187e4e9509` | None | 3254 |
| n30dyn4m1c/crt-turtlesoup-ea | `efdf310fec0a` | MIT | 26914 |
| samuelharting/bandz-po3-stdv-cisd | `c71841f1c7d0` | MPL-2.0 | 29513 |
| Prasad1612/smart-money-concept | `12370230ba0a` | None | 161624 |
| carlosrod723/MQL5-Trading-Bot | `1234e3f000c1` | MIT | 413494 |
| foeed/FvgGold-EA | `4fa57db95d8a` | MIT | 32396 |
| SoCloseSociety/TradeBobbyTerminal | `0e382ee4fb62` | NOASSERTION | 1171482 |
| ikyts501-cloud/kelas-trading-itc-smc | `dc481a3587bb` | MIT | 6357 |
| rachid-netizen/www.tradercate.com | `ba2c6966cef8` | None | 7886 |
| Mike061crypto/michael-ict-academy | `72da503073e8` | MIT | 5229 |
| NadirAliOfficial/STAR-EA-v11.20 | `32c601e90beb` | NOASSERTION | 576040 |
| cedinvest/sm-radar-pine | `65f84dc339c9` | NOASSERTION | 11798 |
| mabdullahns007/okf-bundle-for-ict-concepts | `190dc49befdd` | MIT | 38579 |
| mohity24k/ICT-Notes | `44801d6e74c6` | MIT | 1000 |
| luciferalive/FX-Signal-Desk | `3e399ef96085` | MIT | 2996452 |
| Predestinato-source/Curso-Predestinato-FX | `01bc47193643` | MIT | 14435 |
| nbl1960/Superb-instructional-smc | `c856b0478220` | MIT | 16770 |
| RebiccaT/smc-indicator-library | `d1c985f496f3` | MIT | 1720 |
| kayasolomon/poi-liquidity-detector | `951304b33c71` | MIT | 65542 |
| AkhileshSelvan/smc-mcp | `719862b404ec` | MIT | 14445 |
| jerrylin-23/Alpha_Radar | `237209270a7e` | MIT | 26645109 |
| glitchX-Harshit/liquidity-sweep-reversal-bot | `e7e0944f7865` | MIT | 13974078 |
| adichopra009977-dev/smc-strategy-algo | `87c04f828bcb` | MIT | 110802 |
| reuniware/Smart-Money-Sniper | `457047cc22f9` | MIT | 1868092 |
| SiyabongaDlamini/SmartMoney.MQ5 | `fca12ba42893` | Apache-2.0 | 1287353 |
| yuvrajsingh1097/SMC-SCREENER | `2ef163bbd2fb` | MIT | 133594 |
| yuvrajsingh1097/ICT-Silver-Bullet-Strategy-Backtester | `da1a0d0e0534` | MIT | 25531 |
| belligerent2023/killzone-pro | `c9741342c7c7` | Apache-2.0 | 75939 |
| 0xSHAK1B/FVG-VALIDATED-ORDER-BLOCKS | `110e0566b455` | MIT | 10578 |
| BAKOME-Hub/BAKOME_ICT_Institutional | `d10d120c243b` | MIT | 4594 |
| BlackCat-cyber-creator/x402-agent-hub-mcp | `001c18fbc577` | MIT | 50085 |
| juandavidsanchezbonilla160-oss/liquidity-sweep-lab | `60b751bc8fe8` | MIT | 3673 |
| stephenscodee/TRADING-BOT-REVERSAL-LIQUIDITY-FVG-OB- | `a3105c0a9698` | MIT | 3468 |
| rpanchyk/mt5-liquidity-sweep-ind | `06bee7326973` | MIT | 31990 |
| jericoquek/MTF-Liquidity-Dealing-Range | `8dce40420228` | MPL-2.0 | 32738 |
| CedInvest/smc-trading-glossary | `f80c14b78b0b` | None | 5861 |
| Klout9/ict-strat | `067d737e324f` | None | 1077960 |
| tienyong1997-dev/Mastering-ICT-PD-Arrays | `265ddc499c9f` | None | 16292 |
| noahbate/ict-forum-time-wisdom | `36fd36b9efef` | None | 16451 |
| aashutokalshi/pure-ict-nifty-trader | `250d83c8fdb6` | None | 397569 |
| MaweuPaul/smc-strategy-lab | `efb07ab831c7` | MIT | 186208 |

No repository download failed. Every tarball returned HTTP 200.

## D. Web pages attempted with the session `fetch_page` tool

| URL | result |
|---|---|
| https://en.wikipedia.org/wiki/Market_trends | success (title "Market trend - Wikipedia", 17 chunks, Markdown returned) — reachability probe only, not ICT content, not stored |
| https://www.babypips.com/learn/forex | success (title "Learn Forex Trading at School of Pipsology - Babypips.com", 3 chunks) — reachability probe only, not stored |
| https://www.innercircletrader.com/ | `{"error":"Failed to fetch page","status":"error"}` — no HTTP code exposed by the tool |

## E. Text not stored in full because of licence (not an error, a decision)

These repositories were fully downloaded and hashed, but full text is withheld; see `LICENSE_POLICY.md`. Sizes are the sums of their text files.

| repository | text files | total text bytes | stored as |
|---|---|---|---|
| newsqlguru/ict-index | 493 | 62412248 | EXCERPT (≤25-word quotes) |
| globalfxhunter-create/globalfxhunter.github.io | 2 | 9119136 | EXCERPT (≤25-word quotes) |
| SrsBlack/ict-knowledge-library | 667 | 8003311 | EXCERPT (≤25-word quotes) |
| Rouen007/ict-2022-study-room | 99 | 5197012 | EXCERPT (≤25-word quotes) |
| Yousef-Diab/the-algorithm | 196 | 3185507 | EXCERPT (≤25-word quotes) |
| Kyle2077/ict-2022-skill-bundle | 202 | 2088156 | EXCERPT (≤25-word quotes) |
| kwpark090288-pixel/ICT-AutoTrader | 17 | 1537623 | EXCERPT (≤25-word quotes) |
| gitwithuli/ict-wiki-archive | 8 | 869078 | EXCERPT (≤25-word quotes) |
| Mehranrostamy/ICT-Mentorship-2016-Month-1 | 1 | 224049 | EXCERPT (≤25-word quotes) |
| pravinkumardatafreak/ICT-JOURNAL- | 6 | 212364 | EXCERPT (≤25-word quotes) |
| hindsight-finance/Silver-Bullet-AM-Session | 4 | 70896 | EXCERPT (≤25-word quotes) |
| rachid-netizen/www.tradercate.com | 2 | 63402 | EXCERPT (≤25-word quotes) |
| alptheexplorer/ICT-2024-MENTORSHIP | 1 | 59568 | EXCERPT (≤25-word quotes) |
| n4yr13/ICT-Mentorship | 1 | 22402 | EXCERPT (≤25-word quotes) |
| yuvrajsingh1097/ICT-Smart-Money-Trading-Bot | 2 | 14922 | EXCERPT (≤25-word quotes) |
| thino-dev/Optimus-Prime-ICT_EA | 1 | 11767 | EXCERPT (≤25-word quotes) |
| jericoquek/MTF-Liquidity-Dealing-Range | 1 | 9437 | EXCERPT (≤25-word quotes) |
| BaShAh-s/Bashah-Traders | 2 | 8704 | EXCERPT (≤25-word quotes) |
| cedinvest/sm-radar-pine | 2 | 8479 | EXCERPT (≤25-word quotes) |
| Sagar4575/Sessions-and-Killzones | 3 | 6488 | EXCERPT (≤25-word quotes) |
| zakariab0/ozo | 1 | 6260 | EXCERPT (≤25-word quotes) |
| Artprentice/ICT_Contest | 2 | 5539 | EXCERPT (≤25-word quotes) |
| Prasad1612/smart-money-concept | 2 | 5466 | EXCERPT (≤25-word quotes) |
| martin254/Asian-Turtle-Soup-Trading-Bot | 1 | 2230 | EXCERPT (≤25-word quotes) |
| samuelharting/bandz-po3-stdv-cisd | 2 | 1878 | EXCERPT (≤25-word quotes) |
| tickets2themoon/ICTFVG | 1 | 1869 | EXCERPT (≤25-word quotes) |
| brainstrme/ICT-Trading | 1 | 285 | EXCERPT (≤25-word quotes) |
| yuksels2/ICT-FVG-Tool | 1 | 184 | EXCERPT (≤25-word quotes) |
| icthammer/ICT-Mese5-CoreContent | 1 | 76 | EXCERPT (≤25-word quotes) |
| kishore2296/DrMatrix | 1 | 38 | EXCERPT (≤25-word quotes) |
