import os


def get_env(var_dict) -> dict:
    for key, value in var_dict.items():
        value = os.environ.get(key.upper())
        if value is None:
            raise ValueError(f"Required environment variable {key.upper()} is not set")
        var_dict[key] = value
    return var_dict
