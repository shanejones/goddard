# pylint: disable=invalid-name
import argparse
import json
import os
import pathlib
import pprint
import sys

import github
from github.GithubException import GithubException


def delete_previous_comments(commit, created_comment_ids, exchanges):
    comment_starts = tuple({f"# {exchange.capitalize()}" for exchange in exchanges})
    comment_starts += tuple({f"## {exchange.capitalize()}" for exchange in exchanges})
    comment_starts += tuple({f"### {exchange.capitalize()}" for exchange in exchanges})
    for comment in commit.get_comments():
        if comment.user.login not in ("github-actions[bot]", "s0undt3ch"):
            # Not a comment made by this bot
            continue
        if comment.id in created_comment_ids:
            # These are the comments we have just created
            continue
        if not comment.body.startswith(comment_starts):
            # This comment does not start with our headers
            continue
        # We have a match, delete it
        print(f"Deleting previous comment {comment}")
        comment.delete()


def build_row_line(*, current_value, previous_value, higher_is_better=True, percentage=True):
    if percentage is True:
        pct = " %"
    else:
        pct = ""
    if isinstance(current_value, str) or isinstance(previous_value, str):
        if not isinstance(current_value, str):
            current_value = f"{current_value}{pct}"
        if not isinstance(previous_value, str):
            previous_value = f"{previous_value}{pct}"
        return f" \N{DOUBLE EXCLAMATION MARK} | {current_value} | {previous_value} |"
    same = "\N{SNOWFLAKE}"
    if higher_is_better:
        higher = "\N{ROCKET}"
        lower = "\N{COLLISION SYMBOL}"
    else:
        lower = "\N{ROCKET}"
        higher = "\N{COLLISION SYMBOL}"
    row_line = ""
    if current_value > previous_value:
        row_line += f" {higher} | {current_value}{pct} |"
    elif current_value == previous_value:
        row_line += f" {same} | {current_value}{pct} |"
    elif current_value < previous_value:
        row_line += f" {lower} | {current_value}{pct} |"
    row_line += f" {previous_value}{pct} |"
    return row_line


def get_value_for_report(*, results_data, exchange, currency, strategy, timerange, report_name, key, round_cases=0):
    value = results_data[exchange][report_name]["results"][currency][strategy][timerange][key]
    if not isinstance(value, str) and round_cases:
        value = round(value, round_cases)
    return value


def comment_results(options, results_data):
    gh = github.Github(os.environ["GITHUB_TOKEN"])
    repo = gh.get_repo(options.repo)
    print(f"Loaded Repository: {repo.full_name}", file=sys.stderr, flush=True)

    exchanges = set()
    comment_ids = set()
    commit = repo.get_commit(os.environ["GITHUB_SHA"])
    print(f"Loaded Commit: {commit}", file=sys.stderr, flush=True)

    for exchange in sorted(results_data):
        exchanges.add(exchange)
        name = "Current"
        for currency in results_data[exchange][name]["results"]:
            for strategy in results_data[exchange][name]["results"][currency]:
                comment_body = f"# {exchange.capitalize()} - {currency.upper()} - {strategy.capitalize()}\n\n"
                timeranges = results_data[exchange][name]["results"][currency][strategy]
                for timerange in timeranges:

                    comment_body += f"## {timerange}\n\n"

                    previous_report_sha = results_data[exchange]["Previous"]["sha"]
                    previous_report_label = (
                        f"[Previous](https://github.com/{options.repo}/commit/{previous_report_sha})"
                    )
                    comment_body += f"|     |      | Current | {previous_report_label} |\n"
                    comment_body += "|  --: | :--: |     --: |                     --: |\n"

                    # Sort key, making sure buy tags are also sorted, but last in the list
                    buy_tags = []
                    sorted_keys = []
                    for key in sorted(timeranges[timerange]):
                        if key.startswith("buy_signal_"):
                            buy_tags.append(key)
                            continue
                        sorted_keys.append(key)

                    for key in sorted_keys + buy_tags:
                        row_line = "| "
                        if key == "max_drawdown":
                            label = "Max Drawdown"
                            row_line += f" {label } |"
                            current_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Current",
                                key=key,
                                round_cases=4,
                            )
                            previous_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Previous",
                                key=key,
                                round_cases=4,
                            )
                            row_line += build_row_line(
                                current_value=current_value, previous_value=previous_value, higher_is_better=False
                            )
                            comment_body += f"{row_line}\n"
                        elif key == "profit_mean_pct":
                            label = "Profit Mean"
                            row_line += f" {label } |"
                            current_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Current",
                                key=key,
                                round_cases=4,
                            )
                            previous_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Previous",
                                key=key,
                                round_cases=4,
                            )
                            row_line += build_row_line(current_value=current_value, previous_value=previous_value)
                            comment_body += f"{row_line}\n"
                        elif key == "profit_sum_pct":
                            label = "Profit Sum"
                            current_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Current",
                                key=key,
                                round_cases=4,
                            )
                            previous_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Previous",
                                key=key,
                                round_cases=4,
                            )
                            row_line += f" {label } |"
                            row_line += build_row_line(current_value=current_value, previous_value=previous_value)
                            comment_body += f"{row_line}\n"
                        elif key == "profit_total_pct":
                            label = "Profit Total"
                            current_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Current",
                                key=key,
                                round_cases=4,
                            )
                            previous_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Previous",
                                key=key,
                                round_cases=4,
                            )
                            row_line += f" {label } |"
                            row_line += build_row_line(current_value=current_value, previous_value=previous_value)
                            comment_body += f"{row_line}\n"
                        elif key == "winrate":
                            label = "Win Rate"
                            current_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Current",
                                key=key,
                                round_cases=4,
                            )
                            previous_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Previous",
                                key=key,
                                round_cases=4,
                            )
                            row_line += f" {label } |"
                            row_line += build_row_line(current_value=current_value, previous_value=previous_value)
                            comment_body += f"{row_line}\n"
                        elif key == "trades":
                            label = "Trades"
                            current_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Current",
                                key=key,
                            )
                            previous_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Previous",
                                key=key,
                            )
                            row_line += f" {label } |"
                            row_line += build_row_line(
                                current_value=current_value, previous_value=previous_value, percentage=False
                            )
                            comment_body += f"{row_line}\n"
                        elif key == "duration_avg":
                            current_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Current",
                                key=key,
                            )
                            previous_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Previous",
                                key=key,
                            )
                            label = "Average Duration"
                            comment_body += f" {label } | \N{STOPWATCH} | {current_value} | {previous_value} |\n"
                        elif key.startswith("buy_signal"):
                            current_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Current",
                                key=key,
                            )
                            previous_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Previous",
                                key=key,
                            )
                            comment_body += f" {key} | \N{SPORTS MEDAL} | {current_value} | {previous_value} |\n"
                        else:
                            current_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Current",
                                key=key,
                            )
                            previous_value = get_value_for_report(
                                results_data=results_data,
                                exchange=exchange,
                                currency=currency,
                                strategy=strategy,
                                timerange=timerange,
                                report_name="Previous",
                                key=key,
                            )
                            label = key
                            comment_body += f" {label } | | {current_value} | {previous_value} |\n"
                    ft_output = (
                        options.path / "current" / exchange / currency / strategy / f"backtest-output-{timerange}.txt"
                    )
                    comment_body += "\n<details>\n"
                    comment_body += "<summary>Freqtrade Backest Output (click me)</summary>\n"
                    comment_body += f"<pre>{ft_output.read_text().strip()}</pre>\n"
                    comment_body += "</details>\n"
                    comment_body += "\n\n"

                comment = commit.create_comment(comment_body.rstrip())
                print(f"Created Comment: {comment}", file=sys.stderr, flush=True)
                comment_ids.add(comment.id)

    delete_previous_comments(commit, comment_ids, exchanges)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="The Organization Repository")
    parser.add_argument("path", metavar="PATH", type=pathlib.Path, help="Path where artifacts are extracted")

    if not os.environ.get("GITHUB_TOKEN"):
        parser.exit(status=1, message="GITHUB_TOKEN environment variable not set")

    options = parser.parse_args()

    if not options.path.is_dir():
        parser.exit(
            status=1,
            message=f"The directory where artifacts should have been extracted, {options.path}, does not exist",
        )

    reports_info_path = options.path / "reports-info.json"
    if not reports_info_path.exists():
        parser.exit(status=1, message=f"The {reports_info_path}, does not exist")

    reports_info = json.loads(reports_info_path.read_text())
    for exchange in reports_info:
        reports_info[exchange]["Current"] = {
            "results": {},
            "sha": os.environ["GITHUB_SHA"],
            "path": options.path / "current",
        }

    reports_data = {}
    for exchange in reports_info:
        keys = set()
        reports_data[exchange] = {}
        for name in sorted(reports_info[exchange]):
            exchange_results = {}
            reports_data[exchange][name] = {
                "results": exchange_results,
                "sha": reports_info[exchange][name]["sha"],
            }
            results_path = pathlib.Path(reports_info[exchange][name]["path"])
            for _exchange in results_path.glob("*"):
                if _exchange.name != exchange:
                    continue
                for currency in _exchange.glob("*"):
                    exchange_results[currency.name] = {}
                    for strategy in currency.glob("*"):
                        exchange_results[currency.name][strategy.name] = {}
                        for results_file in strategy.rglob("ci-results-*"):
                            exchange_results[currency.name][strategy.name].update(json.loads(results_file.read_text()))

        names = list(reports_data[exchange])
        for name in names:
            for currency in reports_data[exchange][name]["results"]:
                for strategy in reports_data[exchange][name]["results"][currency]:
                    for timerange in reports_data[exchange][name]["results"][currency][strategy]:
                        for key in reports_data[exchange][name]["results"][currency][strategy][timerange]:
                            keys.add(key)
                            for oname in names:
                                if oname == name:
                                    continue
                                oresults = reports_data[exchange][oname]["results"]
                                for part in (currency, strategy):
                                    if part not in oresults:
                                        oresults[part] = {}
                                    oresults = oresults[part]
                                if timerange not in oresults:
                                    oresults[timerange] = {}
                                oresults[timerange].setdefault(key, "n/a")

    pprint.pprint(reports_data)
    try:
        comment_results(options, reports_data)
        parser.exit(0)
    except GithubException as exc:
        parser.exit(1, message=str(exc))


if __name__ == "__main__":
    main()
