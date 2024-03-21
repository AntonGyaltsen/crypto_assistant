# As of 21st Mar 2024, the price of chat-gpt 3.5 turbo is
input_price = 0.0005 / 1000  # price per 1000 tokens
output_price = 0.0015 / 1000  # price per 1000 tokens


class ChatSession:
    """Class to count total cost of session."""

    def __init__(self):
        self.session_total_cost = 0

    def add_to_total_cost(self, amount):
        self.session_total_cost += amount


def llm_cost_calculator_decorator(llm_function):
    """
    A decorator to calculate the input and output cost of ChatGPT.
    This decorator takes llm_function function
    to pass the prompt and get the response.
    """

    def inner_func(*args, **kwargs):
        """
        Calculates the cost of the prompt for a given LLM engine rounded to 4
        decimal places :param args: This is a prompt argument given to
        llm_function :return: Returns the response given by the LLM engine
        """
        # Call the original LLM function
        response = llm_function(*args, **kwargs)
        session = kwargs.pop('session')

        usage_stats = response.usage
        prompt_tokens = getattr(usage_stats, 'prompt_tokens', 0)
        completion_tokens = getattr(usage_stats, 'completion_tokens', 0)
        total_tokens = getattr(usage_stats, 'total_tokens', 0)

        total_cost = ((prompt_tokens * input_price) + (completion_tokens *
                                                       output_price))
        session.add_to_total_cost(total_cost)
        print(f"Prompt tokens: {prompt_tokens}, "
              f"Completion tokens: {completion_tokens}, "
              f"Total tokens: {total_tokens}")
        print(f"The total cost for the below chat completion: "
              f"${total_cost:.4f}")

        return response

    return inner_func
