# Goddard

**A collection of small, simple strategies for Freqtrade.** Simply add the strategy you choose in your strategies folder and run.



> ⚠️ General Crypto Warning
>
> Crypto and crypto markets are very volatile. By using these strategies, you do so at your own risk. We are not to be held accountable for any losses caused. We're not even to be held responsible for any wins you make either.
>
>The results you get will not always be the same as someone else because many factors cause differences in everyone's setups. Server location, server performance, coin lists, config and filter differences, market conditions all play into this.
>
>Don't let greed take over and always manage your own risk and make sure you take profits along the way to recoup your initial investment. Never invest more than you can afford to lose.
>
> *Always do your own backtesting or dry runs before running this strategy live*



# Strategies

Goddard is made up of 2 simple strategies that can be run on any time frame you want. The buy signals for both strategies are the same. They only differ in the way they sell.

Buy Signals can be seen and experimented with over on TradingView.

~~Head to this link https://www.tradingview.com/script/uXtX0WCT-Goddard/ and then scroll down and Add to your Favourite indicators. You can then add this to any chart. Using the settings for the strategy (Hover over the name on the chart, click the settings cog), you can adjust the values used to make those buy decisions.~~

~~If you find a better selection of values that result in better buy signals, be sure to submit these using the issues tracker within GitHub and we'll test and apply to the main repo after backtesting.~~

*TradingView keep blocking my script from the public library. Please ignore the above for now until I resolve it. *

You'll notice these strategies are not fast. Their intention is to hold out for profit. If you want a bot that trades hundreds of times per day, this is not for you. Is it profit you want or more trades?

These strategies work fine with any number of trade slots. During development, most of us used five trade slots. These strategies also work with any number of trade slots. The most we live tested to was 25 trade slots with a coin list of 25. This ensures we don't miss any trades on any coins.


## Saturn5
Uses buy signals to make trades low in a dip or at the start of an uplift. Our aim here is to get out of this trade when we hit 5% profit.

We have a 20% stop loss on this to allow for natural fluctuations at the start of the trade and to also get you out should this trade tank.

The aim of this strategy is to make another trade as soon as a trade sells. In our tests, this strategy always had full slots.

## Apollo11
This strategy is the same as Saturn5, except we remove the 5% fixed profit.

The sell signals here use a custom stop-loss function to help your trades travel as high as possible. This is done by using tiers, so the trailing stop loss changes as your profit rises too. In our tests, we found some trades to exceed 1000% in profit so we're pretty confident this works well.



# For developers

All tests should be done using branches on Git.

## Clone The Repository
If you plan to only clone the repository to use the strategy, a regular ``git clone`` will do.

However, if you plan on running additional strategies or run the test suite, you need to clone
the repository and it's submodules.

### Newer versions of Git

```bash
git clone --recurse-submodules git@github.com:shanejones/goddard.git checkout-path
```

### Older versions of Git

```bash
git clone --recursive git@github.com:shanejones/goddard.git checkout-path
```

### Existing Checkouts
```
git submodule update --remote --checkout
```

## Workflow

Development and test versions should all follow the same branch formatting. Some examples are below
```
dev/Saturn5-new-buy-signal
dev/Apollo11-add-csl-level
fix/Saturn5-fixing-logic
```

Prefix new functionality with `dev` and any bugfixes with `fix`.

Please ensure your commit messages give details on any significant changes

When a branch has been Merged and Squashed with the main branch, the branches will be deleted. If your branch test is unsuccessful in your tests, delete it when you are done. We should try to keep the number of branches minimal if possible.

## Pre-Commit

Code style guidelines and static lint checking is enforced by [pre-commit](https://pre-commit.com).
After cloning the repository, be sure to run the following:

```
pip install pre-commit
pre-commit install --install-hooks
```


# Why Goddard

Robert Goddard was an American physicist who sent the first liquid-fueled rocket aloft in Auburn, Massachusetts, on March 16, 1926. He had two U.S. patents for using a liquid-fueled rocket and also for a two- or three-stage rocket using solid fuel, according to NASA.

In case you haven't guessed, the strategies have space-themed names 🚀
