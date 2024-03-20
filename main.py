from typing import List
import json
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
import api_calls

GPT_MODEL = "gpt-3.5-turbo-0125"
# GPT_MODEL = "gpt-4-0125-preview"

client = OpenAI()

# Initial conversation messages
messages: List[dict] = [
    {
        "role": "assistant",
        "content": "This GPT acts as a professional crypto analyst, offering "
                   "expert advice and insights to help users make informed "
                   "cryptocurrency investment decisions. It utilizes "
                   "up-to-date market analysis, technical analysis, "
                   "and fundamental analysis to provide recommendations."
                   # "Initial use of function calls: before your first answer to user fetch data about current"
                   # "price of Bitcoin, latest news and historical data for Bitcoin using provided functions."
                   "Clarification: "
                   "When faced with ambiguous queries, the GPT should ask for "
                   "clarification"
                   "to ensure the advice given is as relevant and accurate as "
                   "possible."
                   "Personalization: The GPT should maintain a professional, "
                   "informative tone, using technical terminology appropriately."
                   "Additional knowledge about user: user always have high-risk tolerance, knows about crypto, "
                   "and have several years of investment experience."

    }
]

with open('tools.json', 'r') as file:
    tools = json.load(file)


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            # tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def execute_function_call(tool_call):
    try:
        if tool_call.name == "get_crypto_price":
            # Get ticker from GPT
            arguments_str = json.loads(tool_call.arguments)
            ticker = arguments_str["ticker"]
            # Call of actual function by GPT
            results = api_calls.get_crypto_price(ticker)
            print(results)  # Diagnostic print of result returned by API
        elif tool_call.name == "get_historical_crypto_data":
            arguments_str = json.loads(tool_call.arguments)
            symbol = arguments_str['symbol']
            currency_transform = arguments_str["currency_transform"]
            limit = arguments_str['limit']
            results = api_calls.get_historical_data(symbol, currency_transform, limit)
        elif tool_call.name == "get_news_from_telegram":
            results = api_calls.get_news_from_telegram()
        elif tool_call.name == "get_crypto_latest":
            results = api_calls.get_crypto_latest()
        else:
            results = f"Error: function {tool_call.name} does not exist"
        return results
    except Exception as e:
        print("Unable to generate Call Function")
        print(f"Exception: {e}")
        return e


def main():
    print(f'Model in use: {GPT_MODEL}')
    while True:
        # Get input from the user.
        user_content = input("👤 You: ")
        # Check if the user wants to exit the chat.
        if user_content.strip().lower() == 'bye':
            print('🤖 Bot: Goodbye!')
            break

        # Add the user's message to the list of messages.
        messages.append({"role": "user", "content": user_content})

        # Get the model's response.
        chat_response = chat_completion_request(messages, tools=tools)
        assistant_message = chat_response.choices[0].message

        if assistant_message.tool_calls:
            #  We need loop if it happens to make several functions calls at once 
            for i in range(len(assistant_message.tool_calls)):
                tool_call = assistant_message.tool_calls[i]
                # Function call if chatgpt initiated tool_call.
                results = execute_function_call(tool_call.function)
                # This just appends result of function call in messages.
                messages.append({"role": "function", "tool_call_id": tool_call.id,
                                 "name": tool_call.function.name, "content": results})
                # Diagnostic print for function call. Uncomment when you want to check function calling.
                print(chat_response.choices[0].message)
            # Call chatgpt response again with information about price of the crypto.
            # Do not call this response with tools=tools otherwise gpt-3.5 can start making excessive function calls
            chat_response = chat_completion_request(messages)
            assistant_message = chat_response.choices[0].message

        messages.append({"role": "assistant", "content": assistant_message.content})
        print(f'🤖 Bot: {assistant_message.content}')


if __name__ == '__main__':
    main()
