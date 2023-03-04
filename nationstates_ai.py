import json
import requests
import xml.etree.ElementTree as ElementTree
import logging
import time

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


def huggingface_query(payload, headers, url):
    while True:
        response = json.loads(
            requests.request("POST", url, headers=headers, json=payload).content.decode("utf-8"))
        try:
            testing_dict = response["answer"]
            del testing_dict
            return response
        except KeyError:
            print("AI is offline, retrying in 30 seconds...")
            logging.error("AI is offline, retrying in 30 seconds...")
            time.sleep(30)


def get_issues(nation, password, user_agent):
    url = f"https://www.nationstates.net/cgi-bin/api.cgi"
    headers = {"X-Password": password, "User-Agent": user_agent}
    params = {"nation": nation, "q": "issues"}
    response = requests.request("GET", url, headers=headers, params=params)
    print(response.headers)
    x_pin = response.headers["X-pin"]
    response = response.text
    with open("issues.txt", "a") as myfile:
        myfile.write(response)
    logging.info(response)
    print(response)
    response = ElementTree.fromstring(response)
    issue_list = []
    for issue in response[0]:
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
    return [issue_list, x_pin]


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


def execute_issues(nation: str, password: str, issues: list, x_pin: str, hf_headers: str, hf_url, prompt: str,
                   user_agent):
    logging.info(f"Executing {len(issues)} issues...")
    execute = []
    for issue in issues:
        logging.info(f"Contacting AI...")
        selected_option = huggingface_query(
            {
                "inputs": {
                    "question": format_question(issue, prompt),
                    "context": format_issue(issue),
                }
            }, hf_headers, hf_url
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
            selected_option = issue.options[selected_option-1].id
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
        headers = {"X-Password": password, "User-Agent": user_agent, "X-Pin": x_pin}
        params = {"nation": nation, "c": "issue", "issue": issue.id, "option": selected_option}
        issue_response = requests.request("GET", issue_execution_url, headers=headers, params=params)
        print(str(issue_response.headers))
        execute.append(issue_response.text)
        with open("issue_results.txt", "a") as myfile:
            myfile.write(issue_response.text)
        if issue_response.status_code == 200:
            logging.info(f"Executed issue.")
        else:
            logging.info(f"Issue execution failed with error code {issue_response.status_code}")
            print(f"Issue execution failed with error code {issue_response.status_code}")
            return execute
    return execute


def time_to_next_issue(nation: str, password: str, x_pin: str, user_agent):
    url = "https://www.nationstates.net/cgi-bin/api.cgi"
    headers = {"X-Password": password, "User-Agent": user_agent, "X-Pin": x_pin}
    params = {"nation": nation, "q": "nextissuetime"}
    response = requests.request("GET", url, headers=headers, params=params)
    return response


def ns_ai_bot(nation, password, headers, hf_url, prompt, user_agent):
    while True:
        issues = get_issues(nation, password, user_agent)
        execute_issues(nation, password, issues[0], issues[1], headers, hf_url, prompt, user_agent)
        next_issue = time_to_next_issue(nation, password, issues[1], user_agent).text
        next_issue_time = int(ElementTree.fromstring(next_issue)[0].text) \
                          - time.time() + 10
        logging.info(f"Sleeping {next_issue_time} seconds until next issue...")
        print(f"Sleeping {next_issue_time} seconds until next issue...")
        time.sleep(next_issue_time)
