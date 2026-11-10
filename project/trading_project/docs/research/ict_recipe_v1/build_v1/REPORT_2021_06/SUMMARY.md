# SUMMARY — real_2021_06

- decisions: **6336**; plans: **106**; no-plan: **6230**
- window: 5760 bars; bars consumed: 36886; elapsed: 42.911 s
- peak RSS: 82064 kB of 4034452 kB; cap 2824116 kB
- stopped early: None

## 1. No-plan reasons

| reason | count | share |
|---|---|---|
| outside_session_window | 5544 | 87.5% |
| range_position_premium | 221 | 3.5% |
| range_position_discount | 219 | 3.5% |
| zone_not_touched | 110 | 1.7% |
| no_zone_in_direction | 107 | 1.7% |
| range_position_undefined | 13 | 0.2% |
| no_target_ahead | 10 | 0.2% |
| criteria_conflict | 6 | 0.1% |

## 2. Per-step statistics (how often each concept was found)

| step | occurrences | per decision |
|---|---|---|
| swing | 14573 | 2.300 |
| fvg | 8152 | 1.287 |
| order_block | 2 | 0.000 |
| order_block_created | 21 | 0.003 |
| dealing_range | 6247 | 0.986 |
| liquidity_pool_formed | 15225 | 2.403 |
| pool_taken | 26903 | 4.246 |
| sweep | 4748 | 0.749 |
| displacement | 14217 | 2.244 |
| structure_shift | 12337 | 1.947 |
| bias_defined | 36862 | 5.818 |

## 3. R statistics (hypothetical, after half-spread cost)

- settled plans: 106; expired: 0; still open at the end: 0
- mean R -0.807; median -1.140; sum -85.588
- max drawdown in R (cumulative, ordered by exit): -8.050
- longest negative-R streak: 25
- measured R:R to T1: min 0.16, median 2.86, max 50.50 (n=106)
- measured R:R to T2: min 0.35, median 6.45, max 95.00 (n=96); plans with only one target: 10
- stop distance (price): min 0.00002, median 0.00017, max 0.00110

## 4. Fault locator (HYPOTHESIS, one row per settled plan)

| category | plans |
|---|---|
| execution assumption / stop | 63 |
| stop | 25 |
| none visible | 18 |

| plan | verdict | category | evidence |
|---|---|---|---|
| `plan:2021-06-01T06:10:00+00:00:fvg:bullish:30620` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-02T06:25:00+00:00:fvg:bearish:30910` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-02T06:30:00+00:00:fvg:bearish:30910` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-02T07:20:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-02T07:40:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-02T07:30:00+00:00:fvg:bearish:30918` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-02T07:35:00+00:00:fvg:bearish:30918` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-03T08:40:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-04T06:00:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-04T06:40:00+00:00:fvg:bearish:31480` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-04T07:00:00+00:00:fvg:bearish:31462` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-04T07:40:00+00:00:fvg:bearish:31462` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-04T07:50:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-04T08:45:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-07T06:10:00+00:00:sweep:low:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-07T06:25:00+00:00:sweep:low:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-07T06:40:00+00:00:sweep:low:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-07T06:45:00+00:00:sweep:low:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-07T08:05:00+00:00:fvg:bullish:31794` | settled_stop | stop | the stop was touched before T1 |
| `plan:2021-06-07T08:15:00+00:00:fvg:bullish:31794` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-08T06:10:00+00:00:fvg:bullish:32063` | settled_stop | stop | the stop was touched before T1 |
| `plan:2021-06-08T08:25:00+00:00:sweep:low:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-09T06:05:00+00:00:fvg:bearish:32348` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-09T06:10:00+00:00:fvg:bearish:32327` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-09T06:15:00+00:00:fvg:bearish:32327` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-09T07:00:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-09T07:25:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-09T07:50:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-10T06:55:00+00:00:fvg:bullish:32643` | settled_stop | stop | the stop was touched before T1 |
| `plan:2021-06-10T08:15:00+00:00:sweep:low:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-10T08:55:00+00:00:fvg:bullish:32672` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-11T06:10:00+00:00:sweep:high:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-11T07:40:00+00:00:fvg:bearish:32944` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-14T06:00:00+00:00:sweep:low:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-14T06:05:00+00:00:fvg:bullish:33202` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-14T07:10:00+00:00:sweep:low:None` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-14T08:25:00+00:00:fvg:bullish:33232` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-14T08:35:00+00:00:fvg:bullish:33232` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |
| `plan:2021-06-14T08:55:00+00:00:fvg:bullish:33232` | settled_target | none visible | T1 touched before the stop under the conservative rule |
| `plan:2021-06-15T06:00:00+00:00:fvg:bullish:33501` | settled_stop | execution assumption / stop | the triggering bar spanned the whole zone, so the conservative stop-first rule settles it on the entry bar |

## 5. Ranked: what is missing / what looks wrong

- 5544 decisions (88%) fall outside the declared EURO_0200_0500 window; the story state is mostly idle and the window is doing most of the filtering
- the conservative stop-first rule settles plans on their entry bar when a bar spans the zone; the entry/stop model, not the reading, may be the cause
- KNOWLEDGE_GAP: FVG_INVALIDATION — a gap is never 'invalidated', only closed through, so zone lifetimes are mechanical rather than doctrinal
- T2 is a second element of a ranking that was built for one target; whether T2 is a real objective is unsettled

## 6. Non-plan sample (seed 20261109)

The ten sampled non-plan decisions:

| at | reason | close | range position | zones | targets |
|---|---|---|---|---|---|
| 2021-06-08T07:05:00+00:00 | range_position_premium | 1.21812 | premium |  | 1 |
| 2021-06-02T09:00:00+00:00 | outside_session_window | 1.21841 | discount |  | 5 |
| 2021-06-21T04:00:00+00:00 | outside_session_window | 1.18588 | premium |  | 2 |
| 2021-06-11T08:45:00+00:00 | range_position_discount | 1.2167400000000002 | discount |  | 2 |
| 2021-06-24T21:55:00+00:00 | outside_session_window | 1.19291 | discount |  | 5 |
| 2021-06-06T23:20:00+00:00 | outside_session_window | 1.21649 | premium |  | 5 |
| 2021-06-17T06:10:00+00:00 | range_position_discount | 1.19835 | discount |  | 5 |
| 2021-06-15T16:55:00+00:00 | outside_session_window | 1.2124 | premium |  | 4 |
| 2021-06-08T06:05:00+00:00 | range_position_premium | 1.2183400000000002 | premium |  | 1 |
| 2021-06-01T05:30:00+00:00 | outside_session_window | 1.22202 | discount |  | 0 |

The three closest to becoming a plan (a zone existed and price was nearest to it):

| at | distance to zone edge | zone | reason |
|---|---|---|---|
| 2021-06-14T08:20:00+00:00 | 9.999999999843467e-06 | fvg:bullish:33232 | zone_not_touched |
| 2021-06-29T06:25:00+00:00 | 9.999999999843467e-06 | fvg:bearish:36330 | zone_not_touched |
| 2021-06-04T06:45:00+00:00 | 2.0000000000131024e-05 | fvg:bearish:31480 | zone_not_touched |

## 7. Files and hashes

| file | sha256 |
|---|---|
| `MANIFEST.json` | `c374b92ceee7972adf3204412fa33bac2c2abbdb67424f56befdc96feca7d524` |
| `cases/CASE_001.md` | `b975399ceaa716a43d6d3db29f0ced0a8b280bb65beabadf54084e5bbcd5441a` |
| `cases/CASE_002.md` | `e574a2c9da5879eb756ea74d58105fe48ab943987988e29205cd3afb00d3227c` |
| `cases/CASE_003.md` | `c23dc5f291763ef58e8fc0102d16dda3cbf29fe885391bb9f534fb4fc2d68b91` |
| `cases/CASE_004.md` | `faab7bf2411735a15cf589758d921c5af8b76ab098a4c0d698d695a87ff423d6` |
| `cases/CASE_005.md` | `9ce6a978ee1bbd4b886b87d9898bd6634ede8071dc7410cfb26539edc91b5fcd` |
| `cases/CASE_006.md` | `36f74f04af80289cab3f263ce577667b361a6d63ed823228a52f62724ae2ce34` |
| `cases/CASE_007.md` | `94a111fe52bbe7b38f1fa33086aab83b38bc1982c9ef1cfd04986df01d0f61e5` |
| `cases/CASE_008.md` | `1d020e8da610c5344902acf62ded55643c93936fd8e75baa094ff683d8423032` |
| `cases/CASE_009.md` | `6ae73e3e0c714632e3dcfb88b9aaa03b285b1d12b799aad89bb86c4e9426e975` |
| `cases/CASE_010.md` | `ecc8af71fab4bc7a1de0b2cf2afc8e09291a197aae2e1d80b1dc5293163e73f9` |
| `cases/CASE_011.md` | `e63731236ebc9f6705fce2b6c8f7635d5e77b45dcdb6edc22c758330d6acbfd4` |
| `cases/CASE_012.md` | `568e7f56d82f0c1762ad54fe498f4e79e2c4aab1d28f54e30717ec9f4b299444` |
| `cases/CASE_013.md` | `360bad2e86539e9a480ad0ba424f42e25f15d03c49e44db79cab2c308cf93d8e` |
| `cases/CASE_014.md` | `9510b13b31f6910c5ab344840087ad5fb5b0301e21466a2644db0d2b80c5a6c5` |
| `cases/CASE_015.md` | `d226a7a0d3bfe7dbb51b2fe7710a9de5543a6ea5ba1fc3c8caff14d38cc7d84d` |
| `cases/CASE_016.md` | `3ea7d5350131ca1686fd1cea50ec6d67227aeb98e4c34565e2ee5acf00d228b3` |
| `cases/CASE_017.md` | `c17349e7181017b5e3396f4f40b556657adbec7db3a3fd8de21acccac4c48e5f` |
| `cases/CASE_018.md` | `df430a106e1aa6d251c06331712ea3afaff1abf74c856e4192f40c9be1774691` |
| `cases/CASE_019.md` | `3bf5f1ab094d57fccf39f5bbd5266a7e9468993f785241a5195bb6ec3ffc0a06` |
| `cases/CASE_020.md` | `4b570926c4ee22f9a4c0ecf92a9bc106ceb78022a8b19707a5a35f4ceda72162` |
| `cases/CASE_021.md` | `f9a6057d22a35fc82dcc7cea52ae03690e8785e49a97f7c76af4aefc5dffacf4` |
| `cases/CASE_022.md` | `45ff24addfb5660f78047ae8b96a859447574d2bc20a95b9e1638db95f956fa7` |
| `cases/CASE_023.md` | `fb765be3c24b07a95ee62c1735bbf755d2ee7c392a14d162558631648c5569f1` |
| `cases/CASE_024.md` | `b2006fa67195891b5f3f1d2a6a0314388c7415a54ce993d9aabec7c762daa763` |
| `cases/CASE_025.md` | `54df807c9df3b448a1fe25b62c1cf557a697f97aa461e573d9f9e2a1e7c83ece` |
| `cases/CASE_026.md` | `f63d2b09ffa84472456c81e3c8a0d334358b27b47c3dbc624da4d7f08c11314f` |
| `cases/CASE_027.md` | `d2ee7696e0381a31a5a743ef77cf28c27da0c1f854deee52e3a8c96ca195cb46` |
| `cases/CASE_028.md` | `4976c3331fe93049976457f445668313259f2f9ff2e2e1d79ed2d993df5eff36` |
| `cases/CASE_029.md` | `7fea607975506612c3180f1afd36b3a7699b944da77dedf37585fd4f5fd22750` |
| `cases/CASE_030.md` | `f9063f7b10db6ade83af49913d9dde16b4f5cd49740d5dc4bef3fb1260331072` |
| `cases/CASE_031.md` | `9da4c9f0209da42bc0062e8246491e1f54c6cf5c730f271b9d88663b4aa36b2d` |
| `cases/CASE_032.md` | `b68310f8935db378264b9c5898338e5235f5e8550c666d4717b62e87e0894e6d` |
| `cases/CASE_033.md` | `ea9a6ef405fb9a53afb2f2ab2b15ce174b1b2fdb7aef73681cac2b1abf35ccc6` |
| `cases/CASE_034.md` | `359792dcf7f38f8580ac14ed144dff2800e69e85ea14d7ec6feac7765016a5f1` |
| `cases/CASE_035.md` | `85b3d16039bebb9429931932f3b2ab7f1596073da8da64b0f88b312d62b2e3f6` |
| `cases/CASE_036.md` | `a93b22e333d077dd5aabb142a43495cd22e23f06d9423267dbdb2e654e216689` |
| `cases/CASE_037.md` | `d56c1b487cba8742bf3591ab68bf42524b5d86479ad9d9a0e3d08cf54491476d` |
| `cases/CASE_038.md` | `f842ed46be70bfe8fb13a224e4d6ad76b20275bbff98932237b766925a022962` |
| `cases/CASE_039.md` | `47d2d7b352f8bd7688f874f2454a5490f26322fb52c05e147cee65729e34222f` |
| `cases/CASE_040.md` | `90630005d315efaa7f9f7c91590f5300f44801329e8b248a5c55abbf1b12c80e` |
| `cases/CASE_041.md` | `62d68d1b176ae41e233f23ae04e472de619b29b6ee0a91fca852d100149e6778` |
| `cases/CASE_042.md` | `d6a3fdf014af379556ef69ede856c829af214799e3df46ca8ad39dc7cac6d889` |
| `cases/CASE_043.md` | `ae8ec5f25dce4b5407c17706b441cffafa5df6fb6ea8d0997954c822d14bc6d4` |
| `cases/CASE_044.md` | `f29305680ccf3d896e698eb92889b1abd657c4a391cbd33c43a572241f957108` |
| `cases/CASE_045.md` | `f6606f6881bba6ca133595314e3dbf61c6f388256a965d8f61fb36190544f152` |
| `cases/CASE_046.md` | `ad90f3d631c513b36ed7f00861ca675d30a8230a4b9d4b8f74f78e569e2413c8` |
| `cases/CASE_047.md` | `3adc5d153298d106de1124bfdb8446e7d9e091d4d56f5d3fec44f36c5f478a56` |
| `cases/CASE_048.md` | `dbf71e8b9e343c5655a23b7bc890a85cbba188c0d7168206cfa79ae03df2cfe3` |
| `cases/CASE_049.md` | `385ed15e3acf93a6e034846b27d692823fa3b23e095fa991bc8f1ad9c90850d6` |
| `cases/CASE_050.md` | `93f4b7870aee915c3e6f1c5504d9a74777f8727f274cd559837898ded461ab08` |
| `cases/CASE_051.md` | `88906cca35fd15c37ccacbacedbc7bc45ddad2b0f372996f2d0dfe364f01d6dc` |
| `cases/CASE_052.md` | `eb80164f2c1f99e27d68e779a777b71fc837fd61b1c48ccf348be79c3c131201` |
| `cases/CASE_053.md` | `c41bb7452f246cc832466e6aa4a3241bf4473c1d41cae751208a79aa4ea5e411` |
| `cases/CASE_054.md` | `c52b630ed5758377f778aa1dfd5d8f4563fa3190a98e8ee5bbace5d1d6e728f0` |
| `cases/CASE_055.md` | `7ec6e006882c4ddd0e90976b456a3d8455908e47c86ee2ae99bdc5b3c5b5234e` |
| `cases/CASE_056.md` | `cd4083d7f76dbcd93329c68175a1105f39d24a7910a2a79dde99fade97bae0c2` |
| `cases/CASE_057.md` | `e34d7fd5de1d29cc711ba5da620c0c6f12f25862ed7f44393519abb9013adbcd` |
| `cases/CASE_058.md` | `4a4ce3ad3904a0cdd9291e652fe5b71b0b9fd22019c54257ab597e0013fe7e39` |
| `cases/CASE_059.md` | `d52c34b5381908a4d88e2c673b0034728a2b47f4474d05967e4d49e26341eeda` |
| `cases/CASE_060.md` | `317ed70e0ba5a6b3bc03a98b0eae2513a7a8c4ebfaad8cd133c26974791582c4` |
| `cases/CASE_061.md` | `911fdfb2d2d6a1862ba7c64a4a32137bf856a5d1fd6a523d84e279a30bcb0000` |
| `cases/CASE_062.md` | `ce5d22da368c3116f6ff5eb6c811827f9b2203122e591a1de2d0238faaad373a` |
| `cases/CASE_063.md` | `7cf7e4bcd78ac469f6986c0e19eb70ff543195b3572ef7885f51727362806f74` |
| `cases/CASE_064.md` | `60082e61338ea784567cf0add9ff9ade0858c57b6faaf9956d17e92eb4ca66d0` |
| `cases/CASE_065.md` | `ba149c803f467844ec1f535f6711df30c770e2b03e71441255e6961e46e3afae` |
| `cases/CASE_066.md` | `fecee4d5dfff1e2de519ceab22b7b8838f06e438ff3ea8bd9aade3b2a5861fbc` |
| `cases/CASE_067.md` | `ea91bdd756880201deaafd8b04e6661285b8d49cc2b9fcea8ed51cf8dd788ab3` |
| `cases/CASE_068.md` | `1576bd7db7a469823c1fef35cf62722dc7ca7ca59191b2973afe18b5bcd77474` |
| `cases/CASE_069.md` | `5076d0cb9b6ff6a946eb5ee614b3021769afc3b4abdfc6e45b75e6fbdcc2b8c6` |
| `cases/CASE_070.md` | `6713e1dc5cb7815005156c7eee861e6d79aa1e7ba57b5fbbf135a506b3084add` |
| `cases/CASE_071.md` | `9bb9502081995a1ccf430b81bfb2a8939a751a183a5ce47a49767cabb5b94ce7` |
| `cases/CASE_072.md` | `ab07824d79cb353c7043fe3faff2ac3129c89cc00c37ac02529761a9b8919b77` |
| `cases/CASE_073.md` | `79421bd07f51a53cffdd0c19621e8a600797e9d827fad0f19911633f6fe0b8c7` |
| `cases/CASE_074.md` | `d307b39ee4ecffaf856bed9da4619638eb54cf9540530c81ec536ce2f69e231c` |
| `cases/CASE_075.md` | `1340cb6457aa83fdc872ba86765b578f0cda178e2847c068712435581500a800` |
| `cases/CASE_076.md` | `817bc46b46e92c437dff90f71c353ff9a769b78b468c9b4f1b4220b0dd0bf605` |
| `cases/CASE_077.md` | `a473053752a35f83a41020b23da2e181385f8752820076af8c78ae6c153459d5` |
| `cases/CASE_078.md` | `84ff2e8c6457fd32eff643e62337bea1b4f53c0de16d2e11adb4a4d37c17c6dc` |
| `cases/CASE_079.md` | `0b5adb9cbd68115ae06e35e97571ec6ca0ef80a01aae50afc2b704c7c2f511eb` |
| `cases/CASE_080.md` | `5b8b2d2f134c8d8374b6c3a29077e9780cf2cc868c3642f6fbee6bb4e7ba3ff3` |
| `cases/CASE_081.md` | `d96bea577285f1d878c2ed88ffb76f3ec487c26b42d3787544f44a7511d24884` |
| `cases/CASE_082.md` | `71795870536c910d3b296c7ba4339af587bca9c3c2820c3058ccf0953add5001` |
| `cases/CASE_083.md` | `4611e3ff980de8c34f353e7d44e87445576a1e266c2bb5f7984f5911df768cdf` |
| `cases/CASE_084.md` | `eae1f2cd6a09f349beb91a250238484626bb15c06be5a5d6ec023ecf00108088` |
| `cases/CASE_085.md` | `b71d7d7a7f4d551befa501351d14148d80eef2c8ba121192247d0ba0fa039047` |
| `cases/CASE_086.md` | `d1113dbd918e0be83109e68e09416265338762eb76342557b38855f03ead84f3` |
| `cases/CASE_087.md` | `2e5369e9cae1b271e85640e94cc38a74ca3e2a7c6adc58de2fd804e81c530b59` |
| `cases/CASE_088.md` | `3de14d37466659045b5af2745d35a92667f253d5a4af4d9c5e277a57dc899344` |
| `cases/CASE_089.md` | `36d73c7c41e21033fc1885b213a75138846bbd19840cd586dbe0c929df206530` |
| `cases/CASE_090.md` | `2d3ac43008d43d0b2678104bd1b3e79b2a6823e10fc60c5b8ebdf52d7d7e6675` |
| `cases/CASE_091.md` | `a6bd35172b4e251658c291eadb32f7178664453ef7f2590cea1429939ef3093e` |
| `cases/CASE_092.md` | `a06672808e832512f196321068baf11ca4af47bfa3946c1d68b1419c4e2b3a04` |
| `cases/CASE_093.md` | `ff55b1cad483f7a05dfb296c5b2596e9a8a74a973907c0e60cccde8c51d0f823` |
| `cases/CASE_094.md` | `d52df7105e7920929af2c1dd15c1c36daf2c7c3b4b4cf4bfc3e0565dd27c7ccd` |
| `cases/CASE_095.md` | `ff3de53500131725143b2d966dc8d3249e7a50852068d0b973c25783350408eb` |
| `cases/CASE_096.md` | `f65c2222ad208f792d58aa54d9e2b6fffc40874cb8803e693d939dad7de4198e` |
| `cases/CASE_097.md` | `30b6fba7eb7fce1f9412729237085cfb8e038799bbb84ef864c5e0c2a5348a9e` |
| `cases/CASE_098.md` | `fdad8ba37f25c629447b7a523f16d0ae140db2b7682eb390dcec99ad57354203` |
| `cases/CASE_099.md` | `323a46d6276da1532492b652ca9aca566cd4edbb5cbb005e80d18c3b344508c0` |
| `cases/CASE_100.md` | `1b7994d6f5c2380050282291ea38897e79343751662c509a3959ae44c28d70c0` |
| `cases/CASE_101.md` | `7bdfe2645057245039741755f9243a9605b7efee38e072c25aa2e43a14594ddf` |
| `cases/CASE_102.md` | `c8e9b9a65d752601e786643aa40999d0dc11d7e22fddc77415fe5447c87faa47` |
| `cases/CASE_103.md` | `13182bec72931b520cee04c8f7ba3a0841cbbbe70322468744ddce866cc751aa` |
| `cases/CASE_104.md` | `5c286ac9a49fc850c18b46670bf56a3834ff86cce1f12c4ad77994f0e6575e99` |
| `cases/CASE_105.md` | `5723893086d032be429007cea8459d5096c0747d9663a83f506131d9fac27fa5` |
| `cases/CASE_106.md` | `b4ef3408ff6b6488487c48119cfd6ffe39d768471e3027906c75a0f206937be2` |
| `decisions.jsonl` | `972f6900b8be41cc76db50097da900c1620649d53bf61d18ff4d1f912f731513` |
| `plans.jsonl` | `4d0eff213080806c1140fc27c12a7957276bd9fc3c71bfd39b8b17030fea0b95` |
| `run_summary.json` | `518208838f88380948dc6abff670976fa641c87df7a09fa78fe62fb410ca378f` |
| `story.jsonl` | `d660f35f2400a0577338c53aeb482efc7a26987ff5396cb2b8f3860709a407d8` |

## What this does NOT establish

- It does not establish that any reading is correct: a plan is `HYPOTHETICAL_` and a settled R is an accounting identity under a stated fill assumption, not a result.
- The fault locator is a **HYPOTHESIS** derived from stored fields, not a diagnosis.
- Zero or few plans is not evidence about the market; it is evidence about the gate chain and the declared window.
- The sensitivity of `WINDOW_BARS` is not tested here (DECLARED_CHOICES row 1).
