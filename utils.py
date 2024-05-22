import datetime
import hashlib
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
        if event_name in ["pull_request", "pull_request_target"]
        else os.environ.get("GITHUB_REF_NAME")
    )
    github_token = os.environ.get("INPUT_REPO_TOKEN")
    gh_repo_rw_token = os.environ.get("GITHUB_REPO_RW_TOKEN")
    github_api_url = os.environ.get("GITHUB_API_URL")
    github_base_repository = os.environ.get("GITHUB_REPOSITORY")
    pr_number = event_payload.get("number", "-1")
    repo_name = (
        event_payload["pull_request"]["head"]["repo"]["full_name"]
        if event_name in ["pull_request", "pull_request_target"]
        else os.environ.get("GITHUB_REPOSITORY")
    )
    compose_file_location = os.environ.get("INPUT_COMPOSE_FILE")


    @staticmethod
    def get_project_url():
        return f"https://github.com/{GitHubHelper.repo_name}.git"

    @staticmethod
    def comment_on_gh_pr(comment):
        if not GitHubHelper.github_token:
            raise Exception("INVALID GITHUB TOKEN _ EMPTY")

        headers = {
            "Authorization": f"Bearer {GitHubHelper.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json",
        }

        comment_identifier_keyword = f"Sarthi Deployment Status {SarthiHelper.get_unique_code()}"

        comment_id = None

        # List current comments on PR
        url = f"{GitHubHelper.github_api_url}/repos/{GitHubHelper.github_base_repository}/issues/{GitHubHelper.pr_number}/comments"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        comment_list = response.json()

        for github_comment in comment_list:
            if (
                "bot" in github_comment["user"]["login"]
                and comment_identifier_keyword in github_comment["body"]
            ):
                comment_id = github_comment["id"]
                break

        if comment_id:
            url = f"{GitHubHelper.github_api_url}/repos/{GitHubHelper.github_base_repository}/issues/comments/{comment_id}"
        else:
            url = f"{GitHubHelper.github_api_url}/repos/{GitHubHelper.github_base_repository}/issues/{GitHubHelper.pr_number}/comments"

        data = {"body": comment_identifier_keyword + "🤖\n" + comment}

        response = requests.post(url, headers=headers, json=data)
        print(f"Tried commenting on GitHub Issue with response {response.text}")
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
    def get_unique_code():
        return hashlib.md5(GitHubHelper.repo_name.encode()).hexdigest()[:16]

    @staticmethod
    def deploy_preview(project_git_url, branch, gh_token):
        body = {
            "project_git_url": project_git_url,
            "branch": branch,
            "compose_file_location": GitHubHelper.compose_file_location,
            "gh_token": gh_token
        }
        response = requests.post(
            url=f"{SarthiHelper._sarthi_server_url}/deploy",
            headers=SarthiHelper._get_headers(),
            data=json.dumps(body),
        )
        response.raise_for_status()
        service_urls = response.json()
        print(f"Successfully deployed ✅ {project_git_url}/{branch}")
        print("\n".join(f"- {url}" for url in service_urls))
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
        print(f"Tried deleting preview environment with response {response.text}")
        return response.text


def handle_push_events():
    SarthiHelper.deploy_preview(
        GitHubHelper.get_project_url(),
        GitHubHelper.branch_name,
        GitHubHelper.github_token
    )


def handle_pr_events():
    action = GitHubHelper.event_payload["action"]
    if action in ["opened", "synchronize", "reopened"]:
        services_url = SarthiHelper.deploy_preview(
            GitHubHelper.get_project_url(),
            GitHubHelper.branch_name,
            GitHubHelper.gh_repo_rw_token
        )
        GitHubHelper.comment_on_gh_pr(
            f"Deployed Services Successfully ✅\n"
            + "\n".join(f"- {url}" for url in services_url)
        )
    elif action == "closed":
        SarthiHelper.delete_preview(
            GitHubHelper.get_project_url(),
            GitHubHelper.branch_name,
        )
        GitHubHelper.comment_on_gh_pr(
            f"Deleted ephemeral / preview environment for {GitHubHelper.get_project_url()}/{GitHubHelper.branch_name}"
        )
    else:
        raise ValueError(f"Unknown action type detected {action}")


def handle_delete_events():
    SarthiHelper.delete_preview(
        GitHubHelper.get_project_url(), GitHubHelper.branch_name
    )
