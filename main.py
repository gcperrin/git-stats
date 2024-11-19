import subprocess
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def run_git_command(command, repo_path):
    """Run a git command in the specified repository and return the output."""
    result = subprocess.run(command, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    return result.stdout.strip()

def get_commits_for_day(date, repo_path):
    """Get the commit hashes and authors for a specific day."""
    command = f'git log --since="{date} 00:00" --until="{date} 23:59" --format="%H|%an"'
    command = f'git log --since="{date} 00:00" --until="{date} 23:59" --format="%H|%an" -- . ":!*.go"'
    # command = f'git log --since="{date} 00:00" --until="{date} 23:59" --format="%H|%an" -- . ":!yarn.lock" ":!.idea/" ":!package-lock.json"'


    commits = run_git_command(command, repo_path).splitlines()
    return [commit.split('|') for commit in commits]  # Returns list of [commit_hash, author]

def get_code_changes(commit, repo_path):
    """Get the number of lines added and deleted for a specific commit."""
    command = f'git show --stat --oneline {commit}'
    output = run_git_command(command, repo_path)
    
    # Parse the output to find the lines added/deleted
    added, deleted = 0, 0

    for line in output.splitlines():
        if 'file changed' or 'files changed' in line:
            parts = line.split(',')
            for part in parts:
                if 'insertion' in part:
                    added += int(part.strip().split()[0])
                elif 'deletion' in part:
                    deleted += int(part.strip().split()[0])
    return added, deleted

def get_changes_per_month(repo_path):
    """Get the lines of code added/deleted per author per day for the last month."""
    today = datetime.now()
    results = {}

    # Dictionary to store total lines added/deleted per author
    totals_by_author = defaultdict(lambda: {'added': 0, 'deleted': 0})

    # Loop through the last 30 days
    for i in range(30):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        commits = get_commits_for_day(date, repo_path)
        
        # Using defaultdict to store changes per author
        changes_by_author = defaultdict(lambda: {'added': 0, 'deleted': 0})
        
        for commit_hash, author in commits:
            added, deleted = get_code_changes(commit_hash, repo_path)
            changes_by_author[author]['added'] += added
            changes_by_author[author]['deleted'] += deleted
            
            # Accumulate totals for each author
            totals_by_author[author]['added'] += added
            totals_by_author[author]['deleted'] += deleted
        
        results[date] = changes_by_author

    # Calculate differential for each author
    for author, totals in totals_by_author.items():
        totals['differential'] = totals['added'] - totals['deleted']

    
    return results, totals_by_author

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Get lines of code changes per author in a Git repo over the last month.")
    parser.add_argument("repo_path", help="The absolute path to the Git repository")
    args = parser.parse_args()

    # Get changes and print them
    changes, totals_by_author = get_changes_per_month(args.repo_path)
    for day, authors in changes.items():
        print(f"{Fore.CYAN}Date: {day}{Style.RESET_ALL}")
        for author, change in authors.items():
            added_text = f"{Fore.GREEN}Lines added: {change['added']}{Style.RESET_ALL}"
            deleted_text = f"{Fore.RED}Lines deleted: {change['deleted']}{Style.RESET_ALL}"
            print(f"  {Fore.YELLOW}Author: {author}{Style.RESET_ALL}, {added_text}, {deleted_text}")

    # Print the total changes by author at the end
    print(f"\n{Fore.CYAN}Total Lines Added and Deleted by Author Over the Last Month:{Style.RESET_ALL}")
    for author, totals in totals_by_author.items():
        total_added_text = f"{Fore.GREEN}Total lines added: {totals['added']}{Style.RESET_ALL}"
        total_deleted_text = f"{Fore.RED}Total lines deleted: {totals['deleted']}{Style.RESET_ALL}"
        differential_text = f"{Fore.MAGENTA}Differential: {totals['differential']}{Style.RESET_ALL}"
        print(f"  {Fore.YELLOW}Author: {author}{Style.RESET_ALL}, {total_added_text}, {total_deleted_text}, {differential_text}")


