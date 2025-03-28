# MergeBot

A simple python script to merge all filtered PRs in a GitHub user/org/repository.

![Example](doc/example.png)

## Usage

1. Download the [`src/run.py`](https://raw.githubusercontent.com/CarmJos/MergeBot/refs/heads/master/src/run.py) file.
2. Install the [PyGithub](https://github.com/PyGithub/PyGithub) library.    
   ```bash
    $ pip install PyGithub tqdm colorama
    ```
    or install the required packages from the requirements.txt file.
   ```bash
    $ pip install -r requirements.txt
    ```
3. Replace `ACCESS_TOKEN` with your token in the `run.py` file.
   - You can create a token at [GitHub/Profile/Tokens](https://github.com/settings/tokens).
4. Run the script with the following command:
    ```bash
    $ python run.py <user/org> [repo]
    ```
> [!TIP]
> You can rewrite the `def pr_filter(pr)` function to filter the PRs you want to merge.
> 
> The default filter is to merge PRs that submitted by @renovate or @dependabot.


## Open Source License

This project is licensed under the [GNU LESSER GENERAL PUBLIC LICENSE](https://www.gnu.org/licenses/lgpl-3.0.html).
