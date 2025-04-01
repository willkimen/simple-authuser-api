import copy
import random
import string


def merge_dict(original_dict: dict, update_data: dict) -> dict:
    """
    Creates a deep copy of the original dictionary, updates it with new data,
    and returns the updated dictionary.

    Args:
        original_dict (dict): The original dictionary to be copied and updated.
        update_data (dict): The dictionary containing data to update the original
                            dictionary with.

    Returns:
        dict: The updated dictionary with new data.
    """
    updated_dict: dict = copy.deepcopy(original_dict)
    updated_dict.update(update_data)
    return updated_dict


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
    characters: str = string.ascii_letters + string.digits
    random_code: str = "".join(random.choice(characters) for _ in range(length))
    return f"{prefix}{random_code}"
