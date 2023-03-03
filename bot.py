from nationstates_ai import ns_ai_bot
import threading
import time
import logging

logging.basicConfig(filename="logs.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

USER_AGENT = "insert_your_own_user_agent"
"""User agents need to include a form of contacting you as per NS API rules."""
HF_API_TOKEN = "insert_token_here"
API_URL = "https://api-inference.huggingface.co/models/distilbert-base-cased-distilled-squad"
NATIONSTATES_PASSWORDS = ["password1", "password2"]
NATION = ["nation1", "nation2"]
PROMPTS = ["Who would Donald Trump agree with,", "Which is the best choice,"]
"""The server will send a question with the format {prompt} 1, 2, 3, or 4?
e.g. Who would Donald Trump agree with, 1, 2, 3, or 4?"""

for index in range(len(NATIONSTATES_PASSWORDS)):
    print(f"Starting up thread {index + 1}...")
    logging.info(f"Starting up thread {index + 1}...")
    ns_ai_thread = threading.Thread(target=ns_ai_bot, args=(
        NATION[index], NATIONSTATES_PASSWORDS[index], {"Authorization": f"Bearer {HF_API_TOKEN}"}, API_URL,
        PROMPTS[index], USER_AGENT))
    ns_ai_thread.start()
    print(f"Started up thread {index + 1}. Waiting 30 seconds before starting up next thread...")
    logging.info(f"Started up thread {index + 1}. Waiting 30 seconds before starting up next thread...")
    time.sleep(30)


