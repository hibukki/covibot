import os


def get_env_message(environment_variable_name):
    return os.environ.get(environment_variable_name).replace("\\n", '\n')
