import random
import string


def generate_random_code(length: int = 8, prefix: str = "") -> str:
    """
    Generates a random alphanumeric code with an optional prefix.

    This function creates a random string of specified length consisting of
    uppercase and lowercase letters, and digits. The code is used for various
    purposes.

    Args:
        length (int): The length of the generated random part of the code.
                      Defaults to 8.
        prefix (str): An optional string to prepend to the generated code.

    Returns:
        str: The generated random alphanumeric code with the optional prefix.
    """
    characters = string.ascii_letters + string.digits
    random_code = "".join(random.choice(characters) for _ in range(length))
    return f"{prefix}-{random_code}"
