import time


def program_timer(func):
    """Print the runtime of the decorated function"""

    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()  # 1
        value = func(*args, **kwargs)
        end_time = time.perf_counter()  # 2
        run_time = end_time - start_time  # 3
        # convert duration to hours, minuts, seconds
        minutes, seconds = divmod(run_time, 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            print(
                "{}{} HOURS {} MINUTES {:6.3f} SECONDS".format(
                    "TOTAL RUN TIME: ", hours, minutes, seconds
                )
            )
        elif minutes > 0:
            print(
                "{}{} MINUTES {:6.3f} SECONDS".format(
                    "TOTAL RUN TIME: ", minutes, seconds
                )
            )
        else:
            print("{}{:6.3f} SECONDS".format("TOTAL RUN TIME: ", seconds))

        return value

    return wrapper_timer
