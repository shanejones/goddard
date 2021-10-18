# pylint: disable=redefined-outer-name
import pytest

from tests.backtests.helpers import Backtest
from tests.backtests.helpers import ExpectedResults
from tests.conftest import REPO_ROOT

RESULTS = ExpectedResults()


@pytest.fixture(scope="session")
def stake_currency(request):
    return request.config.getoption("--stake-currency")


@pytest.fixture(scope="session")
def strategy(request):
    return request.config.getoption("--strategy")


@pytest.fixture(scope="session")
def exchange(request):
    return request.config.getoption("--exchange")


@pytest.fixture(params=RESULTS.timeranges())
def timerange(request):
    return request.param


@pytest.fixture
def expected_result(exchange, strategy, stake_currency, timerange):
    for entry in RESULTS.results:
        if entry.exchange != exchange:
            continue
        if entry.strategy != strategy:
            continue
        if entry.stake_currency != stake_currency:
            continue
        if entry.timerange != timerange:
            continue
        return entry
    pytest.fail(f"Could not find expected_results for {exchange} using {stake_currency} for {strategy} and {timerange}")


@pytest.fixture
def backtest(request, stake_currency, strategy, timerange, exchange, expected_result):
    exchange_data_dir = REPO_ROOT / "user_data" / "data" / expected_result.exchange
    if not exchange_data_dir.is_dir():
        pytest.fail(
            f"There's no exchange data for {expected_result.exchange}. Make sure the repository submodule "
            "is init/update. Check the repository README.md for more information."
        )
    if not list(exchange_data_dir.rglob("*.json.gz")):
        pytest.fail(
            f"There's no exchange data for {expected_result.exchange}. Make sure the repository submodule "
            "is init/update. Check the repository README.md for more information."
        )
    instance = Backtest(
        request,
        stake_currency=stake_currency,
        strategy=strategy,
        timerange=timerange,
        exchange=exchange,
    )
    ret = instance()
    try:
        yield ret
    finally:
        # Let's now make sure the numbers don't deviate much from what we expect
        # so that we always keep these tight
        errors = []
        if ret.stats_pct.winrate - 1 > expected_result.winrate:
            errors.append("winrate")
        if ret.stats_pct.max_drawdown + 1 < expected_result.max_drawdown:
            errors.append("max_drawdown")
        if errors:
            errmsg = (
                f"Please update the {exchange}({stake_currency}) expected "
                f"results for the {strategy} strategy during {timerange}."
            )
            if "max_drawdown" in errors:
                old = expected_result.max_drawdown
                new = int(ret.stats_pct.max_drawdown) + 1
                errmsg += f" Set `max_drawdown` from {old} to {new}."
            if "winrate" in errors:
                old = expected_result.winrate
                new = int(ret.stats_pct.winrate)
                errmsg += f" Set `winrate` from {old} to {new}."
            pytest.fail(errmsg)


def test_expected_values(backtest, expected_result, subtests, exchange, stake_currency, strategy, timerange):
    errmsg = (
        f"If expected, please update {exchange}({stake_currency}) expected "
        f"results for the {strategy} strategy during {timerange}."
    )
    with subtests.test("Winrate"):
        winrate_errmsg = f"Winrate results got worse. {errmsg} Set `winrate` to {int(backtest.stats_pct.winrate)}"
        assert backtest.stats_pct.winrate >= expected_result.winrate, winrate_errmsg
    with subtests.test("Max Drawdown"):
        max_drawdown_errmsg = (
            f"Max Drawdown results got worse. {errmsg} "
            f"Set `max_drawdown` to {int(backtest.stats_pct.max_drawdown + 1)}"
        )
        assert backtest.stats_pct.max_drawdown <= expected_result.max_drawdown, max_drawdown_errmsg
