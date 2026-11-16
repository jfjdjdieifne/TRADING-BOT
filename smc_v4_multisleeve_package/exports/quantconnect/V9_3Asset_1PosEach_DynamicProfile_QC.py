# QUANTCONNECT.COM - V9 Dynamic Profile 3-Asset Sniper
# Upload this launcher together with smc_core.py and smc_execution.py.
# The split keeps every file below QuantConnect Cloud's 32,000-character limit
# without removing or approximating any strategy logic.

from AlgorithmImports import *
from smc_core import V9ProfileMixin
from smc_execution import V9ExecutionMixin


class V9DynamicProfile3AssetAlgorithm(V9ProfileMixin, V9ExecutionMixin, QCAlgorithm):
    pass
