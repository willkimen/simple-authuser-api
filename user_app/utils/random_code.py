import random
import string


def generate_random_code(length=8):
    """
    Generates a random alphanumeric code.

    This function creates a random string of specified length consisting of
    uppercase and lowercase letters, and digits. The code is used for various
    purposes such as activating accounts, changing passwords, resetting passwords,
    and changing emails.

    Args:
        length (int): The length of the generated code. Defaults to 8.

    Returns:
        str: The generated random alphanumeric code.
    """
    characters = string.ascii_letters + string.digits
    random_code = "".join(random.choice(characters) for _ in range(length))
    return random_code
