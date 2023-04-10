from nationstates_ai import ns_ai_bot
import asyncio
import logging
import json
import aiosqlite
import time
import os
import sys

logging.basicConfig(
    filename="logs.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

USER_AGENT = os.environ.get("USER_AGENT", "i.didnt.set.a.user.agent@disappointed.sad AI Issue Answering")
"""User agents need to include a form of contacting you as per NS API rules."""
try:
    HF_API_TOKEN = os.environ["HF_API_TOKEN"]
except KeyError:
    print("Input your Huggingface API token into your .env file under the name of HF_API_TOKEN.")
    sys.exit(0)
API_URL = os.environ.get("API_URL", "https://api-inference.huggingface.co/models/distilbert-base-cased-distilled-squad")
try:
    NATIONS = json.loads(os.environ["NATIONS"])
except KeyError:
    print("Input your Nationstates nations into your .env file under the name of NATIONS. "
          "See an example .env file at https://github.com/Bohaska/nationstates_ai/blob/main/.env.")
    sys.exit(0)
try:
    NATIONSTATES_PASSWORDS = json.loads(os.environ["NATIONSTATES_PASSWORDS"])
except KeyError:
    print("Input your Nationstates passwords into your .env file under the name of NATIONSTATES_PASSWORDS. "
          "See an example .env file at https://github.com/Bohaska/nationstates_ai/blob/main/.env.")
    sys.exit(0)
try:
    PROMPTS = json.loads(os.environ["PROMPTS"])
except KeyError:
    print("Input the prompts for your nations into your .env file under the name of PROMPTS. "
          "See an example .env file at https://github.com/Bohaska/nationstates_ai/blob/main/.env.")
    sys.exit(0)


async def run_all_ais(
        user_agent, hf_api_token, api_url, ns_passwords, nations, prompts
):
    con = await aiosqlite.connect("nationstates_ai.db")
    ns_ai_coroutines = []
    counter = 0
    for index in range(len(ns_passwords)):
        cursor = await con.execute("SELECT name FROM sqlite_master WHERE name='next_issue_time'")
        table = await cursor.fetchone()
        if table is not None:
            cursor = await con.execute(
                "SELECT timestamp FROM next_issue_time WHERE nation = ?",
                (nations[index],),
            )
            timestamp = await cursor.fetchone()
            if timestamp is not None:
                if timestamp[0] > time.time():
                    ns_ai_coroutines.append(
                        ns_ai_bot(
                            nations[index],
                            ns_passwords[index],
                            {"Authorization": f"Bearer {hf_api_token}"},
                            api_url,
                            prompts[index],
                            user_agent,
                            timestamp[0] - time.time() + 10,
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
    await con.close()
    thing = await asyncio.gather(*ns_ai_coroutines)
    return thing


asyncio.run(
    run_all_ais(
        USER_AGENT, HF_API_TOKEN, API_URL, NATIONSTATES_PASSWORDS, NATIONS, PROMPTS
    )
)
