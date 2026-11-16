"""
ict_vision — a chart-reading engine, not a rule sheet.

Design contract (the whole package obeys this):

1. NO BARE NUMBERS AS DECISION GATES.
   Every quantity that decides a trade is either
     (a) dimensionless (measured in units of the market's own locally-estimated
         volatility sigma, or as a fraction of a range), or
     (b) estimated from the data itself, causally, walk-forward, with a stated
         prior, and then reported so a human can audit it.
   A "40%" style constant is only acceptable when it is a *definition*
   (e.g. the midpoint of a gap is 50% by geometry) — never as a fitted gate.

2. EVERYTHING IS CONTINUOUS.
   Confluence is a smooth membership / log-likelihood-ratio, so 40.1% scores
   0.97 instead of being rejected by an `== 40` test.

3. EVERYTHING IS CAUSAL.
   No array may be built with information from the future of the bar it is
   indexed at. `tests/test_causality.py` enforces this mechanically.

4. THE ENGINE EXPLAINS ITSELF.
   Every decision emits a narrative that names the structure it saw, why the
   level matters, where the number came from and how much evidence it carries.
"""

__version__ = "1.0.0"
