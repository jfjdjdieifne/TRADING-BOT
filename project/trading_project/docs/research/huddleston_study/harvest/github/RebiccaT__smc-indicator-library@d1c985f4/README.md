# smc-indicator-library

Building blocks for Smart Money Concepts and ICT indicators, in Pine Script and MQL5. Each piece is small enough to read in one sitting and documented well enough to trust.

MIT licensed. Use them, change them, ship them.

## What goes in here

structure/ holds swing detection, break of structure and change of character, with the swing definition exposed as an input rather than hardcoded.

zones/ holds order blocks, breakers, mitigation and fair value gaps, including the fill rules that differ between methods.

liquidity/ holds equal highs and lows, stop run detection, and premium and discount range calculation.

dashboards/ holds multi-timeframe panels that read all of the above across several timeframes at once.

## The rule everything here follows

A level or signal is committed only once the bar that confirms it has closed, and it does not move afterwards. Where a method genuinely needs the unconfirmed view, the file provides both and states which is which.

Higher-timeframe data is requested without lookahead in both languages. If you find a case where that is not true, open an issue. That is a bug, not a preference.

## What each file tells you

Every file opens with a header stating what it does, which bar its output confirms on, and what it cannot see. Inputs are named for what a trader calls them, not for the variable behind them.

## Notes

Open source lives here. Client work stays private.

Corrections and issues are welcome.
