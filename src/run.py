from github import Auth, Github, Repository
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Back, Style
import sys

# Replace with your own GitHub token.
# See https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token
ACCESS_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
THREAD = 4  # Thread count, default 4.


def pr_filter(pr):
    if pr.draft:
        return False
    if pr.user.login in ["dependabot[bot]", "renovate[bot]"]:
        return True
    return False


def repo_filter(repo):
    if repo.archived: return False;
    return True


def prefix(color: Fore, status, name):
    return f"{color}[{status}] {Fore.RESET}<{Fore.LIGHTBLUE_EX}{name}{Fore.RESET}>"

def handle_repo(r: Repository):
    if not repo_filter(r):
        tqdm.write(f"{prefix(Fore.MAGENTA, "START", r.name)} Repo filtered, skipped.")

    try:
        pull_requests = r.get_pulls(state='open')
        pr_list = list(pull_requests)
        pr_count = len(pr_list)

        if pr_count == 0:
            tqdm.write(f"{prefix(Fore.MAGENTA, "START", r.name)} No PRs found, skipped.")
            return
        tqdm.write(f"{prefix(Fore.MAGENTA, "START", r.name)} with {pr_count} PRs, processing.")

        stats = {'skipped': 0, 'done': 0, 'errors': 0}
        with tqdm(pr_list, desc=f"{r.name:15}", leave=False) as pbar:
            for pr in pbar:
                if not pr_filter(pr):
                    stats['skipped'] += 1
                    pbar.set_postfix_str(f"S:{stats['skipped']} D:{stats['done']} E:{stats['errors']}")
                    continue
                try:
                    pr.merge(
                        commit_title=f"[Auto Merge] {pr.title}",
                        merge_method="rebase",
                        delete_branch=True
                    )
                    stats['done'] += 1
                except Exception as ex:
                    stats['errors'] += 1
                    tqdm.write(f"{prefix(Fore.RED, 'ERROR', r.name)} Failed to process #{pr.id}: {str(ex)}")
                finally:
                    pbar.set_postfix_str(f"S:{stats['skipped']} D:{stats['done']} E:{stats['errors']}")
        tqdm.write(
            f"{prefix(Fore.RED, 'DONE', r.name)} "
            f"MERGED: {stats['done']}  "
            f"SKIPPED: {stats['skipped']}  "
            f"ERRORS: {stats['errors']} "
        )
    except Exception as ex:
        tqdm.write(f"{prefix(Fore.RED, 'ERROR', r.name)} Failed to process : {str(ex)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <ORG/USER> [REPO]")
        sys.exit(1)

    auth = Auth.Token(ACCESS_TOKEN)
    github = Github(auth=auth)
    target = sys.argv[1]
    repo_name = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        user = github.get_organization(target)
    except:  # Get user if organization not found.
        user = github.get_user(target)

    if repo_name:
        handle_repo(user.get_repo(repo_name))
    else:
        repos = list(user.get_repos())
        if not repos:
            print(f"No repositories found in {target}")
            sys.exit(0)

        print(f"Found {len(repos)} repositories in {target}")

        with ThreadPoolExecutor(max_workers=THREAD) as executor:
            futures = [executor.submit(handle_repo, repo) for repo in repos]

            with tqdm(total=len(repos), unit="repo", desc="Repositories Progress") as main_pbar:
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as ex:
                        tqdm.write(f"{Fore.RED}[ERROR] Thread error : {str(ex)}")
                    finally:
                        main_pbar.update(1)

    print(Style.RESET_ALL)
    print("All task completed.")
