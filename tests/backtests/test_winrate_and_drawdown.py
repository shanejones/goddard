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
def backtest(request, stake_currency, strategy, expected_result):
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
        timerange=expected_result.timerange,
        exchange=expected_result.exchange,
    )
    ret = instance()
    return ret


def test_expected_values(backtest, expected_result, subtests):
    with subtests.test("Winrate"):
        assert backtest.stats_pct.winrate >= expected_result.winrate
    with subtests.test("Max Drawdown"):
        assert backtest.stats_pct.max_drawdown <= expected_result.max_drawdown
