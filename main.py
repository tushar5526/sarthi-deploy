import os

from utils import (
    GitHubHelper,
    handle_delete_events,
    handle_pr_events,
    handle_push_events,
)


def main() -> None:
    event_name = GitHubHelper.event_name

    if event_name == "pull_request":
        handle_pr_events()
    elif event_name == "push":
        handle_push_events()
    elif event_name == "delete":
        handle_delete_events()
    else:
        raise ValueError("‼️Unsupported event types")


if __name__ == "__main__":
    main()
