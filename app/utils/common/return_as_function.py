from functools import wraps


def returns_a_function_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        def delayed_execution_function():
            return func(*args, **kwargs)
        return delayed_execution_function

    return wrapper