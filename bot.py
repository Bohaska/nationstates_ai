from nationstates_ai import ns_ai_bot
import asyncio
import logging
import dotenv
import json

logging.basicConfig(filename="logs.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

dotenv.load_dotenv(dotenv.find_dotenv())
env_variables = dotenv.dotenv_values()

USER_AGENT = env_variables["USER_AGENT"]
"""User agents need to include a form of contacting you as per NS API rules."""
HF_API_TOKEN = env_variables["HF_API_TOKEN"]
API_URL = env_variables["API_URL"]
NATIONSTATES_PASSWORDS = json.loads(env_variables["NATIONSTATES_PASSWORDS"])
NATIONS = json.loads(env_variables["NATIONS"])
PROMPTS = json.loads(env_variables["PROMPTS"])


async def run_all_ais(user_agent, hf_api_token, api_url, ns_passwords, nations, prompts):
    ns_ai_coroutines = []
    for index in range(len(ns_passwords)):
        ns_ai_coroutines.append(ns_ai_bot(
            nations[index], ns_passwords[index], {"Authorization": f"Bearer {hf_api_token}"}, api_url,
            prompts[index], user_agent, index))
    thing = await asyncio.gather(*ns_ai_coroutines)
    return thing

loop = asyncio.get_event_loop()
loop.run_until_complete(run_all_ais(USER_AGENT, HF_API_TOKEN, API_URL, NATIONSTATES_PASSWORDS, NATIONS, PROMPTS))
