# Prefix-invariance contract (M0)

A later recognizer or narrator is admissible only if it has a pure, sequence-valued
adapter with this meaning:

```text
trace = function(candles)
trace[i] = state at candles[i].end, using candles[:i+1] and nothing later
len(trace) == len(candles)
function([]) == []
```

`trading_system.ict_engine.causal.assert_prefix_invariance` evaluates the full
trace and truncated traces. For every requested prefix `n`, it requires:

```text
function(candles[:n]) == function(candles)[:n]
```

Comparison is exact and includes ordering. The default checks every prefix,
including the empty prefix. Long real-data tests may enumerate explicit prefix
lengths to avoid quadratic work, but synthetic tests for every recognizer must
check all prefixes. A sequence returning only a final summary is not testable by
this harness and therefore is not an admissible engine trace; its per-bar adapter
must be exposed.

The harness is a test, not a claim that arbitrary Python can be proved causal.
Later code must also avoid mutating inputs or retaining results between calls.
Unit tests include a passing running-maximum trace and a deliberately failing
trace that reads the final close, so the check is known to detect lookahead.

Candle labels are UTC **bar starts**. Output at index `i` becomes available only
at the exclusive end (`start + 5 minutes`). This convention applies to M1
primitives, M2 narration, and any later story matcher.
