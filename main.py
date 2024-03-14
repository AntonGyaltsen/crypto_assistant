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
                   "and fundamental analysis to provide recommendations. Do not check latest news until user"
                   "explicitly asks you for the news."
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

tools: List[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_crypto_price",
            "description": "Fetches the current price of a specified cryptocurrency from CoinMarketCap.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The symbol of the cryptocurrency for which to fetch the price, such as 'BTC' for Bitcoin or 'ETH' for Ethereum."
                    }
                },
                "required": ["ticker"]
            },
            "responses": {
                "type": "object",
                "properties": {
                    "price": {
                        "type": "number",
                        "description": "The latest market price of the requested cryptocurrency in USD."
                    }
                }
            },
            "errors": {
                "type": "object",
                "properties": {
                    "error_code": {
                        "type": "integer",
                        "description": "The HTTP status code representing the type of error encountered during the API call."
                    },
                    "error_message": {
                        "type": "string",
                        "description": "A detailed message describing the error if the API call is unsuccessful or the input is invalid."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_from_telegram",
            "description": "Retrieves the latest cryptocurrency news from a specified Telegram channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    # This function does not require any parameters.
                },
                "required": []  # No parameters are required.
            },
            "responses": {
                "type": "object",
                "properties": {
                    "news": {
                        "type": "array",
                        "description": "A list containing the latest news items retrieved from the Telegram channel."
                    }
                }
            },
            "errors": {
                "type": "object",
                "properties": {
                    "error_code": {
                        "type": "integer",
                        "description": "The HTTP status code indicating the type of error that occurred."
                    },
                    "error_message": {
                        "type": "string",
                        "description": "A message describing the error encountered when attempting to retrieve news "
                                       "from Telegram."
                    }
                }
            }
        }
    }
]


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


def execute_function_call(message):
    if message.tool_calls[0].function.name == "get_crypto_price":
        # Get ticker from GPT
        arguments_str = json.loads(message.tool_calls[0].function.arguments)
        ticker = arguments_str["ticker"]
        # Call of actual function by GPT
        results = api_calls.get_crypto_price(ticker)
    else:
        results = f"Error: function {message.tool_calls[0].function.name} does not exist"
    if message.tool_calls[0].function.name == "get_news_from_telegram":
        results = api_calls.get_news_from_telegram()
    return results


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
        # Function call if chatgpt initiated tool_call.
        results = execute_function_call(assistant_message)
        # This just appends result of function call in messages.
        messages.append({"role": "function", "tool_call_id": assistant_message.tool_calls[0].id,
                         "name": assistant_message.tool_calls[0].function.name, "content": results})
        # Diagnostic print for function call. Uncomment when you want to check function calling.
        # print(chat_response.choices[0].message)
        # Call chatgpt response again with information about price of the crypto.
        chat_response = chat_completion_request(messages, tools=tools)
        # Append this response with knowledge about current price to messages.
        messages.append({"role": "assistant", "content": chat_response.choices[0].message.content})
        print(f'🤖 Bot: {chat_response.choices[0].message.content}')
    else:
        messages.append({"role": "assistant", "content": assistant_message.content})
        print(f'🤖 Bot: {assistant_message.content}')
