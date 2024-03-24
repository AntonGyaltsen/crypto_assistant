from datetime import time
from typing import List
import json
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
import api_calls
from additional_methods import llm_cost_calculator_decorator, ChatSession

GPT_MODEL = "gpt-3.5-turbo-0125"
# GPT_MODEL = "gpt-4-0125-preview"

PINK = '\033[95m'
# ANSI escape code for cyan color
CYAN = '\033[96m'
# ANSI escape code for yellow color
YELLOW = '\033[93m'
# ANSI escape code to reset to default color
RESET_COLOR = '\033[0m'

client = OpenAI()
session = ChatSession()  # Session object to count total cost of session.

# Initial conversation messages aka system prompt.
messages: List[dict] = [
    {
        "role": "assistant",
        "content": "This GPT serves as a specialized crypto analyst, "
                   "dedicated to providing advanced and expert advice "
                   "tailored to seasoned investors with a high-risk "
                   "tolerance. It leverages the latest in market trends, "
                   "technical and fundamental analysis, as well as "
                   "cutting-edge research, to deliver nuanced investment "
                   "strategies and insights. Our focus is on empowering users "
                   "to navigate the volatile cryptocurrency markets "
                   "confidently, making well-informed decisions that align "
                   "with their ambitious investment goals. Investment "
                   "Strategy Principle: At the heart of our advisory approach "
                   "is a robust analysis of cryptocurrency price movements, "
                   "initially centered on Bitcoin's historical chart over the "
                   "last 3 months to pinpoint 3-4 critical buying and selling "
                   "levels. This strategy involves investing 25-30% of the "
                   "user's stablecoin reserves at each defined level to buy "
                   "during dips and identifying 3-4 levels to sell during "
                   "price surges, with a flexible timeframe typically "
                   "spanning about a year, contingent upon reaching these "
                   "specified price levels. This basic principle is "
                   "expansively applied to other altcoins that the user may "
                   "be interested in, allowing for a diversified and "
                   "strategic investment approach across the cryptocurrency "
                   "spectrum. Clarification and Interaction: In response to "
                   "queries that are broad or unclear, this GPT is programmed "
                   "to seek additional information. This ensures that the "
                   "insights and recommendations offered are precisely "
                   "tailored to the user's specific circumstances, investment "
                   "profile, and goals. Tone and Language: This GPT adopts a "
                   "professional and authoritative tone, enriched with "
                   "technical jargon and industry terminology. It is designed "
                   "to resonate with individuals who possess a solid "
                   "foundation in cryptocurrency concepts and have a track "
                   "record of engaging with complex investment landscapes. "
                   "User Profile Acknowledgment: This GPT is informed that "
                   "its users possess a robust understanding of the "
                   "cryptocurrency sector, have a propensity for high-risk "
                   "investment opportunities, and bring years of experience "
                   "to their investment strategy discussions. It will use "
                   "this understanding to shape the advice provided, ensuring "
                   "it is appropriate for an audience that is both "
                   "knowledgeable and discerning."

    }
]

with open('tools.json', 'r') as file:
    tools = json.load(file)


@retry(wait=wait_random_exponential(multiplier=1, max=40),
       stop=stop_after_attempt(3))
@llm_cost_calculator_decorator
def chat_completion_request(session=session, messages=messages, tools=None,
                            tool_choice=None, model=GPT_MODEL):
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


@retry(wait=wait_random_exponential(multiplier=1, max=40),
       stop=stop_after_attempt(3))
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
            results = api_calls.get_historical_data(symbol, currency_transform,
                                                    limit)
        elif tool_call.name == "get_news_from_telegram":
            results = api_calls.get_news_from_telegram()
        elif tool_call.name == "get_crypto_latest":
            results = api_calls.get_crypto_latest()
        elif tool_call.name == "search_for_keywords":
            arguments_str = json.loads(tool_call.arguments)
            # print(f"Raw tool_call.arguments: {tool_call.arguments}")
            keyword = arguments_str.get("query")
            results = api_calls.search_for_keywords(keyword)
            print(results)
        elif tool_call.name == "get_binance_data":
            arguments_str = json.loads(tool_call.arguments)
            print(f"Raw tool_call.arguments: {tool_call.arguments}")
            symbol = arguments_str["symbol"]
            how_long = arguments_str["how_long"]
            results = api_calls.get_binance_data(symbol, how_long)
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
        user_content = input(f"👤{PINK} You: {RESET_COLOR}")
        # Check if the user wants to exit the chat.
        if user_content.strip().lower() == 'bye':
            print(f"{YELLOW}Session total cost: "
                  f"${session.session_total_cost:.4f} {RESET_COLOR}")
            print('🤖 Bot: Goodbye!')
            break

        # Add the user's message to the list of messages.
        messages.append({"role": "user", "content": user_content})

        # Get the model's response.
        chat_response = chat_completion_request(session=session,
                                                messages=messages,
                                                tools=tools)
        assistant_message = chat_response.choices[0].message

        if assistant_message.tool_calls:
            # We need loop if it happens to make several functions calls at once
            for i in range(len(assistant_message.tool_calls)):
                tool_call = assistant_message.tool_calls[i]
                # Function call if chatgpt initiated tool_call.
                results = execute_function_call(tool_call.function)
                # This just appends result of function call in messages.
                messages.append({"role": "function",
                                 "tool_call_id": tool_call.id,
                                 "name": tool_call.function.name,
                                 "content": results})
                # Diagnostic print for function call. Uncomment when you want
                # to check function calling.
                print(f'Functions called: {YELLOW} {chat_response.choices[
                    0].message} {RESET_COLOR}')
            # Call chatgpt response again with information about price of the
            # crypto. Do not call this response with tools=tools otherwise
            # gpt-3.5 can start making excessive function calls
            chat_response = chat_completion_request(session=session,
                                                    messages=messages)
            assistant_message = chat_response.choices[0].message

        messages.append({"role": "assistant",
                         "content": assistant_message.content})
        print(f'🤖{CYAN} Bot:{RESET_COLOR} {assistant_message.content}')


if __name__ == '__main__':
    main()
