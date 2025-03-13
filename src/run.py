from github import Auth
from github import Github
from github.Repository import Repository

# 访问秘钥, 请替换为您的GitHub Token
ACCESS_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


# 过滤器，用于判断该PR是否需要自动合并
def pr_filter(pr):
    if pr.state != "open" or pr.draft:
        return False
    if pr.user.login in ["dependabot[bot]", "renovate[bot]"]:
        return True
    return False


def handle_repo(r: Repository):
    pull_requests = r.get_pulls()
    if pull_requests.totalCount == 0:
        print(f"\033[37m>\033[0m {r.full_name} (0) \033[35mSKIPPED\033[0m")
        return

    print(f"\033[37m>\033[0m {r.full_name} ({pull_requests.totalCount})")
    for pr in pull_requests:
        print(f"\033[37m-\033[0m  #{pr.number}\t{pr.user.login}\t{pr.head.ref}\t", end=" ")
        if not pr_filter(pr):
            print("\033[35m[SKIPPED]\033[0m")
            continue
        try:
            pr.merge(
                commit_title=f"[Auto Merge] {pr.title}",
                merge_method="rebase",
                delete_branch=True,
            )
            print("\033[32m[MERGED]\033[0m")
        except Exception as e:
            print(f"An error occurred while trying to merge PR #{pr.number}: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python run.py <OWNER> [REPO]")
        sys.exit(1)

    repo_name = sys.argv[2] if len(sys.argv) > 2 else None

    github = Github(auth=Auth.Token(ACCESS_TOKEN))
    user = github.get_user(sys.argv[1])

    if repo_name is not None:
        handle_repo(user.get_repo(repo_name))
    else:
        repos = user.get_repos()
        if repos.totalCount == 0:
            print(f"No repositories found in {user.name}.")
            sys.exit(0)

        for repo in repos:
            handle_repo(repo)

    print("All done.")
