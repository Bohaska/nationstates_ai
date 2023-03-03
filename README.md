# nationstates-ai
Bridge that answers nationstates issues using an AI

How to set up:
1. Create an account on Huggingface (https://huggingface.co)
2. Generate a read-access token (https://huggingface.co/settings/tokens)
3. Find a host for this bot. I use Daki (https://daki.cc)
4. Create a server. I use 10% CPU, 100mb RAM and 200mb disk storage. Remember to set the programming language as Python.
5. Copy the repository and file names. 
6. Edit python bot.py's environment variables
- USER_AGENT: I use "email@email.com AI Issue Answering" as the user agent, where email@email.com is your actual email.
- HF_API_TOKEN: Input the read-access token you generated in step 2
- API_URL: You can keep this the same. The format is ``https://api-inference.huggingface.co/models/`` plus the model name at the end. The default value is ``https://api-inference.huggingface.co/models/distilbert-base-cased-distilled-squad``.
You can use any question answering model. The list can be found at https://huggingface.co/models?pipeline_tag=question-answering&sort=downloads. To use a model from that collection, copy its name, which is the title showed in search results, and attach it to the end of the url. 
- NATION: Input the corresponding nation names for the passwords you listed above. 

Format: Lowercase, replace all spaces with ``_``, do not keep prefixes like The Republic of Nation

Examples:

Nation -> "nation"

Very Good AI Nation -> "very_good_ai_nation"
- NATIONSTATES_PASSWORDS: Input your Nationstates passwords, one for each nation you want to use the AI to control.
- prompts: Input the prompt you want to give to the AI at the beginning of each issue query. 

The prompts will be sent to the AI in this format: "{prompt} 1, 2, 3 or 4?"

Example: prompt = "Who would Donald Trump agree with,"

Sent query: "Who would Donald Trump agree with, 1, 2, 3, or 4?"
