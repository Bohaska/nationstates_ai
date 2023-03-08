import xml.etree.ElementTree as ElementTree
import logging
import time
import aiohttp
import asyncio

logging.basicConfig(filename="logs.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


class Option:
    __slots__ = 'id', 'text'

    def __init__(self, option_id: int, text: str):
        self.id = option_id
        self.text = text


class Issue:
    __slots__ = 'id', 'title', 'text', 'options'

    def __init__(self, issue_id: int, title: str, text: str, options: list):
        self.id = issue_id
        self.title = title
        self.text = text
        self.options = options


async def manage_ratelimit(nation: str, response: aiohttp.ClientResponse):
    if int(response.headers["X-Ratelimit-Requests-Seen"]) > 30:
        logging.info(f"Pausing nation {nation} for 30 seconds to avoid rate-limits.")
        print(f"Pausing nation {nation} for 30 seconds to avoid rate-limits.")
        await asyncio.sleep(30)
        logging.info(f"Resumed nation {nation} after sleeping for 30 seconds to avoid rate-limits.")
        print(f"Resumed nation {nation} after sleeping for 30 seconds to avoid rate-limits.")


async def parse_issue(issue_text):
    issue_text = ElementTree.fromstring(issue_text)
    issue_list = []
    for issue in issue_text[0]:
        issue_id = int(issue.attrib["id"])
        option_list = []
        for stuff in issue:
            if stuff.tag == "TITLE":
                title = stuff.text
            elif stuff.tag == "TEXT":
                issue_text = stuff.text
            elif stuff.tag == "OPTION":
                option_list.append(Option(option_id=int(stuff.attrib["id"]), text=stuff.text))
        try:
            issue_list.append(Issue(issue_id=issue_id, title=title, text=issue_text, options=option_list))
        except NameError:
            pass
    return issue_list


async def huggingface_query(payload, url, session: aiohttp.ClientSession):
    while True:
        """response = json.loads(
            requests.request("POST", url, headers=headers, json=payload).content.decode("utf-8"))"""
        session = aiohttp.ClientSession(headers=session.headers)
        async with session:
            async with session.post(url, json=payload) as response:
                response = await response.json()
                try:
                    testing_dict = response["answer"]
                    del testing_dict
                    return response
                except KeyError:
                    print("AI is offline, retrying in 30 seconds...")
                    logging.error("AI is offline, retrying in 30 seconds...")
                    time.sleep(30)


async def get_issues(nation, ns_session):
    url = f"https://www.nationstates.net/cgi-bin/api.cgi"
    params = {"nation": nation, "q": "issues"}
    async with ns_session:
        async with ns_session.get(url, params=params) as response:
            await manage_ratelimit(nation, response)
            """logging.info(f"Received cookies: {len(response.cookies)}")
            logging.info(response.headers)"""
            ns_session.headers.add("X-pin", response.headers["X-pin"])
            response = await response.text()
    with open("issues.txt", "a") as myfile:
        myfile.write(response)
    logging.info(response)
    issue_list = await parse_issue(response)
    for issue in issue_list:
        logging.info(format_issue(issue))
        print(f"Issue id {issue.id}: {format_issue(issue)}")
        with open("issues.txt", "a") as myfile:
            myfile.write(format_issue(issue))
    return [issue_list, ns_session]


def format_issue(ns_issue: Issue):
    formatted_issue = f"""{ns_issue.title}

The Issue

{ns_issue.text}

The Debate"""
    index = 1
    for option in ns_issue.options:
        formatted_issue += f"""\n\n{index}. {option.text}"""
        index += 1
    return formatted_issue


def format_question(ns_issue: Issue, prompt: str):
    number_string = ""
    for number in range(1, len(ns_issue.options)):
        number_string += f" {number},"
    number_string += f" or {len(ns_issue.options)}"
    question = f"{prompt}{number_string}? Only input an integer. Other responses will not " \
               f"be accepted."
    return question


async def execute_issues(nation: str, issues: list, hf_url: str, prompt: str,
                         huggingface_session: aiohttp.ClientSession, ns_session: aiohttp.ClientSession):
    logging.info(f"Executing {len(issues)} issues...")
    execute = []
    for issue in issues:
        logging.info(f"Contacting AI...")
        selected_option = await huggingface_query(
            {
                "inputs": {
                    "question": format_question(issue, prompt),
                    "context": format_issue(issue)
                }
            }, hf_url, huggingface_session
        )
        print(str(selected_option))
        selected_option = selected_option["answer"]
        logging.info(f"Response: {selected_option}")
        if "The Debate" in selected_option:
            selected_option = selected_option[12:]
        try:
            selected_option = int(selected_option.strip())
            print(selected_option)
            logging.info(selected_option)
            selected_option = issue.options[selected_option - 1].id
            logging.info(f"Final option ID: {selected_option}")
        except ValueError:
            selected_option = selected_option.strip()
            logging.error(f"Response was not an integer, searching for response in options...")
            for option in issue.options:
                if selected_option in option.text:
                    selected_option = option.id
                    print(f"Found response in option id {selected_option}")
                    break
        logging.info(f"Executing issue...")
        issue_execution_url = f"https://www.nationstates.net/cgi-bin/api.cgi"
        params = {"nation": nation, "c": "issue", "issue": issue.id, "option": selected_option}
        async with ns_session.get(issue_execution_url, params=params) as issue_response:
            if issue_response.status == 200:
                logging.info(f"Executed issue.")
            else:
                logging.info(f"Issue execution failed with error code {issue_response.status}")
                print(f"Issue execution failed with error code {issue_response.status}")
                await manage_ratelimit(nation, issue_response)
                return [execute, aiohttp.ClientSession(headers=ns_session.headers)]
            await manage_ratelimit(nation, issue_response)
            issue_response = await issue_response.text()
        execute.append(issue_response)
        with open("issue_results.txt", "a") as myfile:
            myfile.write(issue_response)
    return [execute, aiohttp.ClientSession(headers=ns_session.headers)]


async def time_to_next_issue(nation: str, ns_session: aiohttp.ClientSession):
    url = "https://www.nationstates.net/cgi-bin/api.cgi"
    params = {"nation": nation, "q": "nextissuetime"}
    async with ns_session:
        async with ns_session.get(url, params=params) as response:
            response = await response.text()
            next_issue_time = int(ElementTree.fromstring(response)[0].text) - time.time() + 10
            return next_issue_time


async def ns_ai_bot(nation, password, headers, hf_url, prompt, user_agent, index: int):
    print(f"""Nation {nation} prepared. 
    Sleeping for {index * 30} seconds before starting to avoid rate limits...""")
    logging.info(f"""Nation {nation} prepared. 
    Sleeping for {index * 30} seconds before starting to avoid rate limits...""")
    await asyncio.sleep(index * 30)
    print(f"""Nation {nation} has woke up and will start automatically answering issues!""")
    logging.info(f"""Nation {nation} has woke up and will start automatically answering issues!""")
    while True:
        ns_session = aiohttp.ClientSession(headers={"X-Password": password, "User-Agent": user_agent})
        issues = await get_issues(nation, ns_session)
        new_session = await execute_issues(nation, issues[0], hf_url, prompt, aiohttp.ClientSession(headers=headers),
                                           issues[1])
        next_issue_time = await time_to_next_issue(nation, new_session[1])
        logging.info(f"Nation {nation} sleeping {next_issue_time} seconds until next issue...")
        print(f"Nation {nation} sleeping {next_issue_time} seconds until next issue...")
        await asyncio.sleep(next_issue_time)
