import json
import os
from datetime import datetime

from config import FLUX_DAILY_LIMIT, FLUX_QUOTA_SECONDS



BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


ACCOUNTS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "hf_accounts.json"
)



def save_accounts(accounts):

    with open(ACCOUNTS_FILE, "w") as file:
        json.dump(
            accounts,
            file,
            indent=4
        )



def initialize_accounts(accounts):

    changed = False


    for account in accounts:

        if "limit_seconds" not in account:

            account["limit_seconds"] = FLUX_DAILY_LIMIT
            changed = True


    return accounts, changed




def load_accounts():

    with open(ACCOUNTS_FILE, "r") as file:
        accounts = json.load(file)


    accounts, changed = initialize_accounts(accounts)


    if changed:
        save_accounts(accounts)


    return accounts


def reset_daily_quota(account):

    today = str(datetime.now().date())


    if account["last_reset"] != today:

        account["used_seconds"] = 0
        account["last_reset"] = today
        account["status"] = "active"



def get_available_token():

    accounts = load_accounts()


    changed = False


    for account in accounts:


        reset_daily_quota(account)


        if account["status"] != "active":
            continue



        remaining = (
            account["limit_seconds"]
            -
            account["used_seconds"]
        )


        if remaining >= 15:


            save_accounts(accounts)


            print(
                f"Using token: {account['name']} | "
                f"Remaining: {remaining}s"
            )


            return account["token"]



    save_accounts(accounts)


    raise Exception(
        "No active HuggingFace ZeroGPU quota available"
    )




def consume_quota(token, seconds=FLUX_QUOTA_SECONDS):


    accounts = load_accounts()


    for account in accounts:


        if account["token"] == token:


            reset_daily_quota(account)


            account["used_seconds"] += seconds


            save_accounts(accounts)


            print(
                f"Quota consumed from {account['name']}: "
                f"+{seconds}s"
            )

            return



def disable_token(token):


    accounts = load_accounts()


    for account in accounts:


        if account["token"] == token:


            account["status"] = "blocked"


            save_accounts(accounts)


            print(
                f"Token disabled: {account['name']}"
            )


            return