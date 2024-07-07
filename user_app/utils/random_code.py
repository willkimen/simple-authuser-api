import random
import string


def generate_random_code(length=8):
    """
    Generate random code to to activate registration, change password, reset password...
    """
    characters = string.ascii_letters + string.digits
    random_code = "".join(random.choice(characters) for _ in range(length))
    return random_code
