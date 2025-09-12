from github import Auth, Github, Repository, PaginatedList
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Back, Style
import sys, os

# Replace with your own GitHub token.
# See https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token
ACCESS_TOKEN = "ghp_xxx"
THREAD = os.cpu_count()


def pr_filter(pr):
    if pr.draft:
        return False
    if pr.user.login in ["dependabot[bot]", "renovate[bot]"]:
        return True
    return False


def repo_filter(owner, repo: Repository):
    if repo.archived: return False;
    if owner.type == "User" and repo.owner.login != owner.login:
        return False
    return True


def prefix(color: Fore, status, name):
    return f"{color}[{status}] {Fore.RESET}<{Fore.LIGHTBLUE_EX}{name}{Fore.RESET}>"


def handle_repo(r: Repository):
    try:
        pull_requests = r.get_pulls(state='open')
        pr_list = list(pull_requests)
        pr_count = len(pr_list)

        if pr_count == 0:
            tqdm.write(f"{prefix(Fore.LIGHTMAGENTA_EX, "SKIP", r.name)} No PRs found, skipped.")
            return
        tqdm.write(f"{prefix(Fore.LIGHTGREEN_EX, "START", r.name)} with {pr_count} PRs, processing.")

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
            f"{prefix(Fore.GREEN, 'DONE', r.name)} "
            f"MERGED: {stats['done']}  "
            f"SKIPPED: {stats['skipped']}  "
            f"ERRORS: {stats['errors']} "
        )
    except Exception as ex:
        tqdm.write(f"{prefix(Fore.RED, 'ERROR', r.name)} Failed to process : {str(ex)}")


if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("You are not providing a specific owner, will use your own account.")
        print("Use 'python run.py [user/organization] [repo]' to specify a target.")

    auth = Auth.Token(ACCESS_TOKEN)
    github = Github(auth=auth)
    target = sys.argv[1] if len(sys.argv) > 1 else None
    repo_name = sys.argv[2] if len(sys.argv) > 2 else None

    owner = github.get_user()  # Current user by default.
    if target:
        try:
            owner = github.get_organization(target)
        except:  # Get user if organization not found.
            target_owner = github.get_user(target)
            if not target_owner:
                print(f"Owner '{target}' not found.")
                sys.exit(1)
            if target_owner.login != owner.login:
                target_owner = target_owner.login

    if repo_name:
        handle_repo(owner.get_repo(repo_name))
    else:
        repos = [repo for repo in owner.get_repos(type='all') if repo_filter(owner=owner, repo=repo)]
        if not repos:
            print(f"No repositories found in {target}")
            sys.exit(0)

        print(f"Found {len(repos)} repositories in {target}")

        with ThreadPoolExecutor(max_workers=THREAD) as executor:
            futures = [executor.submit(handle_repo, repo) for repo in repos]

            with tqdm(total=len(repos), unit="repo", desc="Progress") as main_pbar:
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as ex:
                        tqdm.write(f"{Fore.RED}[ERROR] Thread error : {str(ex)}")
                    finally:
                        main_pbar.update(1)

    print(Style.RESET_ALL)
    print("All task completed.")
