import os

from utils import comment_on_gh_pr, deploy


def main() -> None:
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    github_event = os.environ.get("INPUT_GITHUB_EVENT")
    print(github_event)
    project_url = f"https://github.com/{os.environ.get('INPUT_FORK_REPO_URL') or os.environ.get('GITHUB_REPOSITORY')}.git"
    branch_name = (
        os.environ.get("GITHUB_HEAD_REF")
        if event_name == "pull_request"
        else os.environ.get("GITHUB_REF_NAME")
    )
    sarthi_secret = os.environ.get("INPUT_SARTHI_SECRET")
    sarthi_server_url = os.environ.get("INPUT_SARTHI_SERVER_URL")

    service_urls = deploy(
        project_git_url=project_url,
        branch=branch_name,
        sarthi_secret=sarthi_secret,
        sarthi_server_url=sarthi_server_url,
    )

    comment = ""
    for urls in service_urls:
        comment += urls + "\n"

    if event_name == "push":
        print("Deployed Service URL: \n" + comment)
        return


    comment_on_gh_pr(f"Deployed service URLs\n" + comment)


if __name__ == "__main__":
    main()
