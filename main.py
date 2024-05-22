from utils import (GitHubHelper, handle_delete_events, handle_pr_events,
                   handle_push_events)


def main() -> None:
    event_name = GitHubHelper.event_name

    if event_name in ["pull_request", "pull_request_target"]:
        handle_pr_events()
    elif event_name == "push":
        handle_push_events()
    elif event_name == "delete":
        handle_delete_events()
    else:
        raise ValueError(f"Unsupported event type {event_name}")


if __name__ == "__main__":
    main()
