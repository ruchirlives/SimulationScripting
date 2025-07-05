import os
import ast
from openai import OpenAI


def get_client(api_key: str | None = None) -> OpenAI:
    """Return an OpenAI client using the provided API key or the
    ``OPENAI_API_KEY`` environment variable."""
    key = api_key or os.getenv("OPENAI_API_KEY")
    if key is None:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=key)


def get_openai(prompt: str, *, client: OpenAI | None = None) -> str:
    """Send ``prompt`` to ChatGPT and return the message content."""
    client = client or get_client()
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o",
    )
    return chat_completion.choices[0].message.content


def get_embeddings(text: str, *, client: OpenAI | None = None) -> list[float]:
    """Return embeddings for ``text`` using the ADA model."""
    client = client or get_client()
    response = client.embeddings.create(input=text, model="text-embedding-ada-002")
    return response.data[0].embedding


def generate_summary(text: str, *, client: OpenAI | None = None) -> str:
    """Summarise ``text`` in no more than 25 words."""
    prompt = f"Please provide a summary of the following text in no more than 25 words:\n\n{text}"
    return get_openai(prompt, client=client)


def get_category(text: str, categories: str, prompt: str, *, client: OpenAI | None = None) -> str:
    """Classify ``text`` into one of ``categories``."""
    client = client or get_client()
    full_prompt = (
        f"{prompt} \n"
        "Please classify the entry into one of the following categories, providing only the category by itself in the output. \n\n"
        f"Categories: {categories}\n\nText: {text}"
    )
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who categorises stuff."},
            {"role": "user", "content": full_prompt},
        ],
    )
    return completion.choices[0].message.content


ASSERTION_PROMPT = (
    "Generate a list of structured assertions in Python list-of-dicts format given the input text."\
)


def generate_assertions(text: str, *, client: OpenAI | None = None) -> str:
    """Generate assertions from ``text`` using ``ASSERTION_PROMPT``."""
    client = client or get_client()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": f"{ASSERTION_PROMPT} Here is the text: " + text}],
        model="gpt-4o",
    )
    return response.choices[0].message.content


def extract_assertions(text: str, *, client: OpenAI | None = None):
    """Return a Python object describing assertions extracted from ``text``."""
    try:
        assertions = generate_assertions(text, client=client)
    except Exception:
        # one retry
        assertions = generate_assertions(text, client=client)

    data_string = assertions.replace("```python", "").replace("```", "").strip()
    data_string = data_string.replace("'", r"\'")
    return ast.literal_eval(data_string)
