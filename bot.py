from nationstates_ai import ns_ai_bot
import asyncio
import logging
import dotenv
import json
import sqlite3
import time

logging.basicConfig(
    filename="logs.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

dotenv.load_dotenv(dotenv.find_dotenv())
env_variables = dotenv.dotenv_values()

USER_AGENT = env_variables["USER_AGENT"]
"""User agents need to include a form of contacting you as per NS API rules."""
HF_API_TOKEN = env_variables["HF_API_TOKEN"]
API_URL = env_variables["API_URL"]
NATIONSTATES_PASSWORDS = json.loads(env_variables["NATIONSTATES_PASSWORDS"])
NATIONS = json.loads(env_variables["NATIONS"])
PROMPTS = json.loads(env_variables["PROMPTS"])


async def run_all_ais(
    user_agent, hf_api_token, api_url, ns_passwords, nations, prompts
):
    con = sqlite3.connect("nationstates_ai.db")
    cur = con.cursor()
    ns_ai_coroutines = []
    counter = 0
    for index in range(len(ns_passwords)):
        if cur.execute("SELECT name FROM sqlite_master WHERE name='next_issue_time'").fetchone() is not None:
            timestamp = cur.execute("SELECT timestamp FROM next_issue_time WHERE nation = ?", (nations[index],)).fetchone()[0]
            if timestamp is not None and timestamp > time.time():
                ns_ai_coroutines.append(
                    ns_ai_bot(
                        nations[index],
                        ns_passwords[index],
                        {"Authorization": f"Bearer {hf_api_token}"},
                        api_url,
                        prompts[index],
                        user_agent,
                        timestamp - time.time() + 10,
                    )
                )
        else:
            ns_ai_coroutines.append(
                ns_ai_bot(
                    nations[index],
                    ns_passwords[index],
                    {"Authorization": f"Bearer {hf_api_token}"},
                    api_url,
                    prompts[index],
                    user_agent,
                    counter * 10,
                )
            )
            counter += 1
    con.close()
    thing = await asyncio.gather(*ns_ai_coroutines)
    return thing


loop = asyncio.get_event_loop()
loop.run_until_complete(
    run_all_ais(
        USER_AGENT, HF_API_TOKEN, API_URL, NATIONSTATES_PASSWORDS, NATIONS, PROMPTS
    )
)
