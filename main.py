from openai import OpenAI
import json
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored


GPT_MODEL = "gpt-3.5-turbo-0125"
client = OpenAI()

# Initial conversation messages
messages = [
    {
        "role": "assistant",
        "content": "This GPT acts as a professional crypto analyst, offering "
                   "expert advice and insights to help users make informed "
                   "cryptocurrency investment decisions. It utilizes "
                   "up-to-date market analysis, technical analysis, "
                   "and fundamental analysis to provide recommendations. "
                   "Clarification: "
                   "When faced with ambiguous queries, the GPT should ask for "
                   "clarification"
                   "to ensure the advice given is as relevant and accurate as "
                   "possible."
                   "Personalization: The GPT should maintain a professional, "
                   "informative tone, using technical terminology appropriately"
                   "while also ensuring explanations are accessible to users "
                   "with"
                   " varying levels of crypto knowledge."


    }
]


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "function":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))


while True:
    # Get input from the user
    user_content = input("You: ")

    # Check if the user wants to exit the chat
    if user_content.strip().lower() == 'bye':
        print('Goodbye!')
        break

    # Add the user's message to the list of messages
    messages.append({"role": "user", "content": user_content})

    # Get the model's response
    chat_response = chat_completion_request(messages, tools=tools)

    assistant_content = chat_response.choices[0].message.content
    print(f'Assistant: {assistant_content}')

    # Add the assistant's message to the list of messages
    messages.append({"role": "assistant", "content": assistant_content})




