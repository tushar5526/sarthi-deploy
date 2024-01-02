import datetime
import json
import os

import jwt
import requests


def _get_event_payload():
    with open(os.environ.get("GITHUB_EVENT_PATH")) as file:
        event_payload = json.load(file)
    return event_payload


class GitHubHelper:
    event_payload = _get_event_payload()
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    branch_name = (
        os.environ.get("GITHUB_HEAD_REF")
        if event_name == "pull_request"
        else os.environ.get("GITHUB_REF_NAME")
    )
    github_token = os.environ.get("INPUT_GITHUB_TOKEN")
    github_api_url = os.environ.get("GITHUB_API_URL")
    github_base_repository = os.environ.get('GITHUB_REPOSITORY')

    @staticmethod
    def get_project_url():
        repo_name = (
            GitHubHelper.event_payload["pull_request"]["head"]["repo"]["full_name"]
            if GitHubHelper.event_name == "pull_request"
            else os.environ.get("GITHUB_REPOSITORY")
        )
        return f"https://github.com/{repo_name}.git"

    @staticmethod
    def comment_on_gh_pr(comment):
        if not GitHubHelper.github_token:
            raise Exception("INVALID GITHUB TOKEN _ EMPTY")
        pr_number = os.environ.get("GITHUB_REF_NAME").split("/")[0]

        url = f"{GitHubHelper.github_api_url}/repos/{GitHubHelper.github_base_repository}/issues/{pr_number}/comments"

        headers = {
            "Authorization": f"Bearer {GitHubHelper.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json",
        }
        data = {"body": comment}

        print("headers", headers)
        print("body", data)
        print('url', url)
        response = requests.post(url, headers=headers, json=data)
        print(response.text)
        response.raise_for_status()


class SarthiHelper:
    _sarthi_secret = os.environ.get("INPUT_SARTHI_SECRET")
    _sarthi_server_url = os.environ.get("INPUT_SARTHI_SERVER_URL")

    @staticmethod
    def _get_headers():
        return {
            "Authorization": f"Bearer {SarthiHelper._generate_bearer_token(SarthiHelper._sarthi_secret)}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _generate_bearer_token(secret) -> str:
        payload = {
            "sub": "sarthi",
            "iat": datetime.datetime.utcnow(),  # Issued at time
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(minutes=1),  # Expiration time
        }

        token = jwt.encode(payload, secret, algorithm="HS256")
        return token

    @staticmethod
    def deploy_preview(project_git_url, branch):
        body = {
            "project_git_url": project_git_url,
            "branch": branch,
        }
        response = requests.post(
            url=f"{SarthiHelper._sarthi_server_url}/deploy",
            headers=SarthiHelper._get_headers(),
            data=json.dumps(body),
        )
        response.raise_for_status()
        service_urls = response.json()
        return service_urls

    @staticmethod
    def delete_preview(project_git_url, branch):
        body = {
            "project_git_url": project_git_url,
            "branch": branch,
        }
        response = requests.delete(
            url=f"{SarthiHelper._sarthi_server_url}/deploy",
            headers=SarthiHelper._get_headers(),
            data=json.dumps(body),
        )
        response.raise_for_status()
        service_urls = response.json()
        return service_urls
        pass


def handle_push_events():
    service_urls = SarthiHelper.deploy_preview(
        GitHubHelper.get_project_url(),
        GitHubHelper.branch_name,
    )
    print("Services Deployed Successfully ✅")
    print(service_urls)


def handle_pr_events():
    action = GitHubHelper.event_payload["action"]
    if action == "opened":
        services_urls = SarthiHelper.deploy_preview(
            GitHubHelper.get_project_url(),
            GitHubHelper.branch_name,
        )
        GitHubHelper.comment_on_gh_pr(
            f"Deployed Services Successfully ✅\n{','.join(services_urls)}"
        )
    elif action == "closed":
        SarthiHelper.delete_preview(
            GitHubHelper.get_project_url(),
            GitHubHelper.branch_name,
        )
        print(
            f"Deleted ephemeral / preview environment for {GitHubHelper.get_project_url()}/{GitHubHelper.branch_name}"
        )
    else:
        raise ValueError("Unknown action type detected")


def handle_delete_events():
    pass
