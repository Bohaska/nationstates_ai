from nationstates_ai import ns_ai_bot
import threading
import time
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

for index in range(len(NATIONSTATES_PASSWORDS)):
    print(f"Starting up thread {index + 1}...")
    logging.info(f"Starting up thread {index + 1}...")
    ns_ai_thread = threading.Thread(target=ns_ai_bot, args=(
        NATIONS[index], NATIONSTATES_PASSWORDS[index], {"Authorization": f"Bearer {HF_API_TOKEN}"}, API_URL,
        PROMPTS[index], USER_AGENT))
    ns_ai_thread.start()
    print(f"Started up thread {index + 1}. Waiting 30 seconds before starting up next thread...")
    logging.info(f"Started up thread {index + 1}. Waiting 30 seconds before starting up next thread...")
    time.sleep(30)
