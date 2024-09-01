import copy


def merge_dict(original_dict, update_data):
    """
    Creates a deep copy of the original dictionary, updates it with new data, and returns the updated dictionary.

    Args:
        original_dict (dict): The original dictionary to be copied and updated.
        update_data (dict): The dictionary containing data to update the original dictionary with.

    Returns:
        dict: The updated dictionary with new data.
    """
    updated_dict = copy.deepcopy(original_dict)
    updated_dict.update(update_data)
    return updated_dict
