import argparse
import json
import locale
import logging
import logging.handlers as handlers
import math
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pause

from src import (
    Browser,
    DailySet,
    Login,
    MorePromotions,
    PunchCards,
    ReadToEarn,
    Searches,
)
from src.loggingColoredFormatter import ColoredFormatter
from src.notifier import Notifier


def main():
    while 1:
        setup_logging()
        args = argument_parser()
        notifier = Notifier(args)
        loaded_accounts = setup_accounts()
        accounts_stats = restart_account_counters(loaded_accounts)
        remove_sessions_folder()
        log_account_status(loaded_accounts, accounts_stats)
        while not all(account["done"] for account in accounts_stats):
            for i, account in enumerate(loaded_accounts):
                try:
                    execute_bot_if_proceeds(
                        account, accounts_stats, args, i, loaded_accounts, notifier
                    )
                except Exception as e:
                    logging.exception(f"{e.__class__.__name__}: {e}")
                    bot_pause(pause_time=1, unit="minutes")
                    accounts_stats[i] = True
        bot_pause(pause_time=30, unit="minutes")
        restart_account_counters(loaded_accounts)


def execute_bot_if_proceeds(
    account, accounts_stats, args, i, loaded_accounts, notifier
):
    if not accounts_stats[i]["done"]:
        log_start_account(account, i, loaded_accounts)
        points_earned = execute_bot(account, notifier, args)
        if math.isclose(locale.atof(points_earned), 0.0, rel_tol=0.1, abs_tol=0.1):
            accounts_stats[i]["done"] = True
        accounts_stats[i]["points_earned"] = points_earned
        log_account_status(loaded_accounts, accounts_stats)


def log_account_status(loaded_accounts, accounts_stats):
    for i, current_account in enumerate(loaded_accounts):
        account_str = f"{current_account.get("username", "")}"
        points_earned_str = f"{" - " + accounts_stats[i]["points_earned"] + " points" if "points_earned" in accounts_stats[i] and accounts_stats[i]["points_earned"] and accounts_stats[i]["points_earned"] != "0" else ""}"
        if accounts_stats[i]["done"]:
            logging.info(f"{"[BOT STATUS] ✅ " + account_str + points_earned_str}")
        else:
            logging.info(f"{"[BOT STATUS] 🟥 " + account_str + points_earned_str}")


def bot_pause(pause_time: float, unit: str = "hours"):
    if unit not in ["hours", "minutes"]:
        raise ValueError("Invalid unit. Use 'hours' or 'minutes'.")
    if unit == "hours":
        pause_duration = timedelta(hours=pause_time)
    else:
        pause_duration = timedelta(minutes=pause_time)
    resume_time = datetime.now() + pause_duration
    logging.warning(
        f"[BOT STATUS] ////////////////////  Pause until {resume_time}  \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\n\n"
    )
    pause.until(resume_time)


def restart_account_counters(loaded_accounts):
    return [{"done": False, "points_earned": "0"} for _ in range(len(loaded_accounts))]


def log_start_account(current_account, i, loaded_accounts):
    logging.info(
        "[ACCOUNT]  ************************************************************************************"
    )
    logging.info(
        f'[ACCOUNT]  {i + 1}/{len(loaded_accounts)} - {current_account.get("username", "")}'
    )
    logging.info(
        "[ACCOUNT]  ************************************************************************************"
    )


def remove_sessions_folder():
    logging.info("Remove sessions folder")
    shutil.rmtree("./sessions", ignore_errors=True)


def setup_logging():
    custom_format = "%(asctime)s [%(levelname)s] %(message)s"
    terminal_handler = logging.StreamHandler(sys.stdout)
    terminal_handler.setFormatter(ColoredFormatter(custom_format))

    (Path(__file__).resolve().parent / "logs").mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=custom_format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                "logs/activity.log",
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminal_handler,
        ],
    )


def argument_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Microsoft Rewards Farmer")
    parser.add_argument(
        "-v", "--visible", action="store_true", help="Optional: Visible browser"
    )
    parser.add_argument(
        "-l", "--lang", type=str, default=None, help="Optional: Language (ex: en)"
    )
    parser.add_argument(
        "-g", "--geo", type=str, default=None, help="Optional: Geolocation (ex: US)"
    )
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        default=None,
        help="Optional: Global Proxy (ex: http://user:pass@host:port)",
    )
    parser.add_argument(
        "-t",
        "--telegram",
        metavar=("TOKEN", "CHAT_ID"),
        nargs=2,
        type=str,
        default=None,
        help="Optional: Telegram Bot Token and Chat ID (ex: 123456789:ABCdefGhIjKlmNoPQRsTUVwxyZ 123456789)",
    )
    parser.add_argument(
        "-d",
        "--discord",
        type=str,
        default=None,
        help="Optional: Discord Webhook URL (ex: https://discord.com/api/webhooks/123456789/ABCdefGhIjKlmNoPQRsTUVwxyZ)",
    )
    return parser.parse_args()


def setup_accounts() -> dict:
    account_path = Path(__file__).resolve().parent / "accounts.json"
    if not account_path.exists():
        account_path.write_text(
            json.dumps(
                [{"username": "Your Email", "password": "Your Password"}], indent=4
            ),
            encoding="utf-8",
        )
        no_accounts_notice = """
    [ACCOUNT] Accounts credential file "accounts.json" not found.
    [ACCOUNT] A new file has been created, please edit with your credentials and save.
    """
        logging.warning(no_accounts_notice)
        exit()
    loaded_accounts = json.loads(account_path.read_text(encoding="utf-8"))
    return loaded_accounts


def execute_bot(current_account, notifier: Notifier, args: argparse.Namespace):
    with Browser(mobile=False, account=current_account, args=args) as desktopBrowser:
        account_points_counter = Login(desktopBrowser).login()
        starting_points = account_points_counter
        logging.info(
            f"[POINTS] You have {desktopBrowser.utils.format_number(account_points_counter)} points on your account !"
        )
        DailySet(desktopBrowser).complete_daily_set()
        PunchCards(desktopBrowser).complete_punch_cards()
        MorePromotions(desktopBrowser).complete_more_promotions()
        (
            remaining_searches,
            remaining_searches_m,
        ) = desktopBrowser.utils.get_remaining_searches()
        ReadToEarn(desktopBrowser).complete_read_to_earn()
        if remaining_searches != 0:
            account_points_counter = Searches(desktopBrowser).bing_searches(
                remaining_searches
            )

        if remaining_searches_m != 0:
            desktopBrowser.close_browser()
            with Browser(
                mobile=True, account=current_account, args=args
            ) as mobileBrowser:
                Login(mobileBrowser).login()
                account_points_counter = Searches(mobileBrowser).bing_searches(
                    remaining_searches_m
                )
        points_earned = desktopBrowser.utils.format_number(
            account_points_counter - starting_points
        )
        logging.info(f"[POINTS] You have earned {points_earned} points today !")
        logging.info(
            f"[POINTS] You are now at {desktopBrowser.utils.format_number(account_points_counter)} points !\n"
        )

        notifier.send(
            "\n".join(
                [
                    "Microsoft Rewards Farmer",
                    f"Account: {current_account.get('username', '')}",
                    f"Points earned today: {desktopBrowser.utils.format_number(account_points_counter - starting_points)}",
                    f"Total points: {desktopBrowser.utils.format_number(account_points_counter)}",
                ]
            )
        )
        return f"{desktopBrowser.utils.format_number(account_points_counter)}"


if __name__ == "__main__":
    main()
