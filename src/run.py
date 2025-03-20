from github import Auth, Github, Repository
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Back, Style
import sys

# 访问秘钥和线程配置
ACCESS_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
THREAD = 4  # 默认线程数量


def pr_filter(pr):
    """优化后的PR过滤器，假设已通过state='open'过滤"""
    if pr.draft:
        return False
    if pr.user.login in ["dependabot[bot]", "renovate[bot]"]:
        return True
    return False


def handle_repo(r: Repository):
    try:
        pull_requests = r.get_pulls(state='open')
        pr_list = list(pull_requests)
        pr_count = len(pr_list)

        if pr_count == 0:
            tqdm.write(f"{Fore.MAGENTA}[START] {Fore.RESET}<{Fore.LIGHTBLUE_EX}{r.name}{Fore.RESET}> No PRs found, skipped.")
            return
        tqdm.write(f"{Fore.MAGENTA}[START] {Fore.RESET}<{Fore.LIGHTBLUE_EX}{r.name}{Fore.RESET}> with {pr_count} PRs.")

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
                    tqdm.write(
                        f"{Fore.RED}[ERROR] {Fore.RESET}<{Fore.BLUE}{r.name}{Fore.CYAN}#{pr.number}{Fore.RESET}>"
                        f" Failed to process : {str(ex)}"
                    )
                finally:
                    pbar.set_postfix_str(f"S:{stats['skipped']} D:{stats['done']} E:{stats['errors']}")
        tqdm.write(
            f"{Fore.GREEN}[DONE] {Fore.RESET}<{Fore.LIGHTBLUE_EX}{r.name}{Fore.RESET}> "
            f"MERGED: {stats['done']}  "
            f"SKIPPED: {stats['skipped']}  "
            f"ERRORS: {stats['errors']} "
        )
    except Exception as ex:
        tqdm.write(f"{Fore.RED}[ERROR] <{Fore.BLUE}{r.name}{Fore.RESET}> Failed to process : {str(ex)}")


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

            with tqdm(total=len(repos), unit="repo",desc="Repositories Progress") as main_pbar:
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as ex:
                        tqdm.write(f"{Fore.RED}[ERROR] Thread error : {str(ex)}")
                    finally:
                        main_pbar.update(1)

    print(Style.RESET_ALL)
    print("All task completed.")
