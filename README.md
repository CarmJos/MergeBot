# MergeBot

A simple python script to merge all filtered PRs in a GitHub user/org/repository.

## Usage

1. Download the `src/run.py` file.
2. Install the [PyGithub](https://github.com/PyGithub/PyGithub) library.    
   ```bash
    $ pip install PyGithub
    ```
3. Replace `ACCESS_TOKEN` with your token in the `run.py` file.
   - You can create a token at [GitHub/Profile/Tokens](https://github.com/settings/tokens).
4. Run the script with the following command:
    ```bash
    $ python run.py <user> [repo]
    ```
[!NOTE]
> You can rewrite the `def pr_filter(pr)` function to filter the PRs you want to merge.
> 
> The default filter is to merge PRs that submitted by @renovate or @dependabot.


## Open Source License

This project is licensed under the [GNU LESSER GENERAL PUBLIC LICENSE](https://www.gnu.org/licenses/lgpl-3.0.html).
