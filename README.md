## Sarthi Deploy <img alt="action-badge" src="https://img.shields.io/badge/Sarthi-white?logo=github-actions&label=GitHub%20Action&labelColor=white&color=0064D7"> <a href="https://github.com/lnxpy/cookiecutter-pyaction"><img alt="cookiecutter-pyaction" src="https://img.shields.io/badge/cookiecutter--pyaction-white?logo=cookiecutter&label=Made%20with&labelColor=white&color=0064D7"></a>

Easy to setup Docker based Ephemeral previews!

Pre-requisites 🛠️
-----------------

1. This action is meant to be used in parallel with a self-hosted [Sarthi]() service.
2. Get the secrets generate from that service and add it to the repository's secret. See [creating-secrets-for-a-repository](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository) by GitHub.

Usage 🔄
-------
```yml

name: Sarthi Preview Environments
on:
  pull_request:
  push:

jobs:
  sarthi_job:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v2

      - name: Set up Sarthi
        uses: tushar5526/sarthi-deploy@main
        with:
          compose_file: docker-compose.yml # override this with the compose file name
          sarthi_server_url: ${{ secrets.SARTHI_SERVER_URL }} 
          sarthi_secret: ${{ secrets.SARTHI_SECRET }} # Secret text generate while setting up the server
          fork_repo_url: ${{ github.event.pull_request.head.repo.full_name }}
          GITHUB_TOKEN: ${{ github.token }}
```

### License 📄
This action is licensed under some specific terms. Check [here](LICENSE) for more information.