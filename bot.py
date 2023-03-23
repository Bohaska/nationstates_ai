from nationstates_ai import ns_ai_bot
import asyncio
import logging
import dotenv
import json
import aiosqlite
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
