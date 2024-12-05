import sys
import subprocess
import time
import platform
import argparse
import shutil
import os
import textwrap
import requests
import zipfile
import io

def print_ascii_art():
    print(r"""
     __  __           _      _            _     _
    |  \/  |         (_)    | |          | |   (_)
    | \  / | __ _ ___ _  ___| | _____  __| |__  _ _ __
    | |\/| |/ _` / __| |/ __| |/ / _ \/ _` '_ \| | '_ \
    | |  | | (_| \__ \ | (__|   <  __/ (_| | | | | | | |
    |_|  |_|\__,_|___/_|\___|_|\_\___|\__,_| |_|_|_| |_|

                     Made by Julian
    """)

def run_command(command, cwd=None, capture_output=False, verbose=True, check=True):
    if verbose:
        print(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            check=check,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            text=True
        )
        if capture_output and result.stdout:
            print(result.stdout)
        return result.returncode, result.stdout or '', ''
    except subprocess.CalledProcessError as e:
        output = e.stdout or ''
        if capture_output and output:
            print(f"Error executing: {command}\n{output}")
        else:
            print(f"Error executing: {command}")
        if check:
            sys.exit(1)
        else:
            return e.returncode, output, ''

def install_python_packages(verbose=False):
    required_packages = ['PyGithub', 'requests']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing missing Python package: {package}")
            run_command(f"{sys.executable} -m pip install {package}", capture_output=False, verbose=verbose)

def install_with_chocolatey(package, verbose=False):
    try:
        subprocess.run(
            "choco -v",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except subprocess.CalledProcessError:
        print("Chocolatey is not installed. Please install Chocolatey to install the required packages.")
        print("Visit https://chocolatey.org/install for installation instructions.")
        sys.exit(1)

    print(f"Installing {package} with Chocolatey...")
    run_command(f"choco install {package} -y", capture_output=False, verbose=verbose)

def install_with_apt(package, verbose=False):
    try:
        run_command("sudo apt-get update", capture_output=False, verbose=verbose)
        run_command(f"sudo apt-get install -y {package}", capture_output=False, verbose=verbose)
    except:
        print(f"Error installing {package} with apt. Please install {package} manually.")
        sys.exit(1)

def install_with_homebrew(package, verbose=False):
    try:
        subprocess.run(
            "brew --version",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except subprocess.CalledProcessError:
        print("Homebrew is not installed. Please install Homebrew to install the required packages.")
        print("Visit https://brew.sh/ for installation instructions.")
        sys.exit(1)

    print(f"Installing {package} with Homebrew...")
    run_command(f"brew install {package}", capture_output=False, verbose=verbose)

def check_and_install_git(verbose=False):
    try:
        run_command("git --version", verbose=verbose)
        print("Git is installed.")
    except:
        print("Git is not installed.")
        install_git(verbose=verbose)

def install_git(verbose=False):
    current_os = platform.system()
    if current_os == "Windows":
        install_with_chocolatey("git", verbose=verbose)
    elif current_os == "Linux":
        install_with_apt("git", verbose=verbose)
    elif current_os == "Darwin":
        install_with_homebrew("git", verbose=verbose)
    else:
        print("Automatic installation of Git is not supported on this operating system. Please install Git manually.")
        sys.exit(1)

def check_and_install_gh(verbose=False):
    try:
        run_command("gh --version", verbose=verbose)
        print("GitHub CLI (gh) is installed.")
        # Check if gh is authenticated
        _, auth_status, _ = run_command("gh auth status", capture_output=True, verbose=verbose)
        if "You are not logged into any GitHub hosts" in auth_status:
            print("GitHub CLI is not authenticated. Please authenticate.")
            run_command("gh auth login", capture_output=False, verbose=verbose)
            run_command("gh auth setup-git", capture_output=False, verbose=verbose)
    except:
        print("GitHub CLI (gh) is not installed.")
        install_gh(verbose=verbose)
        print("Please authenticate GitHub CLI.")
        run_command("gh auth login", capture_output=False, verbose=verbose)
        run_command("gh auth setup-git", capture_output=False, verbose=verbose)

def install_gh(verbose=False):
    current_os = platform.system()
    if current_os == "Windows":
        install_with_chocolatey("gh", verbose=verbose)
    elif current_os == "Linux":
        install_with_apt("gh", verbose=verbose)
    elif current_os == "Darwin":
        install_with_homebrew("gh", verbose=verbose)
    else:
        print("Automatic installation of GitHub CLI is not supported on this operating system. Please install GitHub CLI manually.")
        sys.exit(1)

def get_github_token(args):
    token = args.token or os.getenv('GITHUB_TOKEN')
    if not token:
        token = input("Please enter your GitHub Personal Access Token: ").strip()
    if not token:
        print("GitHub Token is required.")
        sys.exit(1)
    return token

def create_repo(repo_name, github_token, verbose=False):
    from github import Github, GithubException

    g = Github(github_token)
    user = g.get_user()
    try:
        repo = user.create_repo(repo_name, private=False, auto_init=False)
        print(f"Repository '{repo_name}' successfully created.")
        return repo
    except GithubException as e:
        print(f"Error creating the repository: {e.data['message']}")
        sys.exit(1)

def upload_project(repo_name, github_token, verbose=False):
    from github import Github

    # Initialize Git repository if not already done
    if not os.path.isdir(".git"):
        print("Initializing Git repository...")
        run_command("git init", capture_output=False, verbose=verbose)

    # Set remote 'origin' to the correct URL
    github_username = get_github_username(github_token)
    remote_url = f"https://github.com/{github_username}/{repo_name}.git"
    print(f"Setting remote 'origin' to {remote_url}")
    run_command("git remote remove origin", capture_output=False, verbose=verbose, check=False)
    run_command(f"git remote add origin {remote_url}", capture_output=False, verbose=verbose)

    # Add files and push
    print("Adding files to Git...")
    run_command("git add .", capture_output=False, verbose=verbose)
    commit_message = "Initial commit"
    returncode, stdout, _ = run_command(f'git commit -m "{commit_message}"', capture_output=True, verbose=verbose, check=False)
    commit_output = stdout.lower() if stdout else ''
    if returncode != 0:
        if "nothing to commit" in commit_output or "working tree clean" in commit_output:
            print("Nothing to commit. Skipping commit step.")
        else:
            print(f"Error during git commit:\n{stdout}")
            sys.exit(1)
    else:
        print("Commit created.")

    print("Pushing files to GitHub...")
    run_command("git branch -M main", capture_output=False, verbose=verbose)
    run_command("git push -u origin main -f", capture_output=False, verbose=verbose)
    print(f"Project successfully uploaded to repository '{repo_name}'.")

def get_github_username(github_token):
    from github import Github

    g = Github(github_token)
    user = g.get_user()
    return user.login

def add_github_actions_workflow(workflow_content, verbose=False):
    workflow_dir = os.path.join('.github', 'workflows')
    os.makedirs(workflow_dir, exist_ok=True)
    workflow_path = os.path.join(workflow_dir, 'build_ios.yml')
    with open(workflow_path, 'w', encoding='utf-8') as f:
        f.write(workflow_content)
    print("GitHub Actions workflow file successfully created locally.")

    # Add the workflow file to git and push
    run_command(f"git add {workflow_path}", capture_output=False, verbose=verbose)
    commit_message = "Add GitHub Actions workflow for iOS build"
    returncode, stdout, _ = run_command(f'git commit -m "{commit_message}"', capture_output=True, verbose=verbose, check=False)
    commit_output = stdout.lower() if stdout else ''
    if returncode != 0:
        if "nothing to commit" in commit_output or "working tree clean" in commit_output:
            print("Workflow file already committed. Skipping commit step.")
        else:
            print(f"Error during git commit:\n{stdout}")
            sys.exit(1)
    else:
        print("Workflow commit created.")

    print("Pushing workflow to GitHub...")
    run_command("git push", capture_output=False, verbose=verbose)
    print("GitHub Actions workflow file successfully pushed to repository.")

    # Wait for GitHub to recognize the new workflow
    print("Waiting for GitHub to recognize the workflow...")
    time.sleep(20)  # Wait for 20 seconds

def set_workflow_permissions(repo_name, github_token, verbose=False):
    print("Setting GitHub Actions permissions to 'Read and write'...")
    owner = get_github_username(github_token)
    url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/permissions"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "enabled": True,
        "allowed_actions": "all",
        "permissions": {
            "contents": "write"
        }
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code in [200, 204]:
        print("GitHub Actions permissions successfully set to 'Read and write'.")
    else:
        print(f"Failed to set GitHub Actions permissions: {response.status_code} - {response.text}")
        sys.exit(1)

def trigger_workflow_dispatch(repo_name, github_token, verbose=False):
    print("Triggering GitHub Actions workflow via API...")
    owner = get_github_username(github_token)
    url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/workflows/build_ios.yml/dispatches"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": "main"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code in [204]:
        print("Workflow dispatch event triggered successfully.")
    else:
        print(f"Failed to trigger workflow dispatch: {response.status_code} - {response.text}")
        sys.exit(1)

def wait_for_workflow_completion(repo, github_token, build_timeout, poll_interval, verbose=False):
    from github import Github

    g = Github(github_token)
    user = g.get_user()
    repository = g.get_repo(f"{user.login}/{repo.name}")
    print("Waiting for the GitHub Actions workflow to start...")
    start_time = time.time()
    workflow_run = None
    while time.time() - start_time < build_timeout:
        # Get the list of workflows
        workflows = repository.get_workflows()
        if workflows.totalCount == 0:
            print("No workflows found in the repository yet. Waiting...")
            time.sleep(poll_interval)
            continue

        # Find the workflow by name
        workflow = next((wf for wf in workflows if wf.name == "iOS Build"), None)
        if not workflow:
            print("Workflow 'iOS Build' not found. Waiting...")
            time.sleep(poll_interval)
            continue

        # Get the runs for the workflow
        runs = workflow.get_runs(branch="main")
        if runs.totalCount == 0:
            print("No workflow runs found. Waiting for the workflow to start...")
            time.sleep(poll_interval)
            continue

        # Get the latest run
        workflow_run = runs[0]
        if workflow_run.status != "completed":
            print(f"Workflow run {workflow_run.id} is in status '{workflow_run.status}'. Waiting for completion...")
            time.sleep(poll_interval)
        else:
            if workflow_run.conclusion == "success":
                print("GitHub Actions workflow completed successfully.")
                if verbose:
                    download_and_display_workflow_logs(repository, workflow_run.id, github_token)
                return
            else:
                print(f"GitHub Actions workflow failed with conclusion: {workflow_run.conclusion}")
                if verbose:
                    download_and_display_workflow_logs(repository, workflow_run.id, github_token)
                sys.exit(1)
    print("Timeout reached. The GitHub Actions workflow did not complete within the expected time.")
    sys.exit(1)

def download_and_display_workflow_logs(repository, run_id, github_token):
    print("Downloading workflow logs...")
    logs_url = f"https://api.github.com/repos/{repository.full_name}/actions/runs/{run_id}/logs"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(logs_url, headers=headers)
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
            for zipinfo in thezip.infolist():
                with thezip.open(zipinfo) as thefile:
                    print(f"\n--- Log file: {zipinfo.filename} ---")
                    log_content = thefile.read().decode('utf-8', errors='ignore')
                    print(log_content)
    else:
        print(f"Failed to download workflow logs: {response.status_code} - {response.text}")

def download_ipa(repo, builds_dir, ipa_name, verbose=False):
    import requests

    print("Fetching the latest release from the repository...")
    releases = repo.get_releases()
    if releases.totalCount == 0:
        print("No releases found.")
        sys.exit(1)
    latest_release = releases[0]
    assets = latest_release.get_assets()
    ipa_asset = None
    for asset in assets:
        if asset.name.endswith(".ipa"):
            ipa_asset = asset
            break
    if not ipa_asset:
        print("No IPA file found in the latest release.")
        sys.exit(1)
    download_url = ipa_asset.browser_download_url
    print(f"IPA download URL: {download_url}")
    os.makedirs(builds_dir, exist_ok=True)
    ipa_path = os.path.join(builds_dir, ipa_name)
    print(f"Downloading the IPA file to '{ipa_path}'...")
    try:
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(ipa_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"IPA successfully downloaded and saved to '{ipa_path}'.")
    except Exception as e:
        print(f"Error downloading the IPA file: {e}")
        sys.exit(1)

def get_workflow_yaml(ipa_name):
    yaml_content = f"""
    name: iOS Build

    on:
      workflow_dispatch:
      push:
        branches:
          - main

    permissions:
      contents: write  # Grants read and write permissions to GITHUB_TOKEN

    jobs:
      build-ios:
        name: iOS Build
        runs-on: macos-latest
        steps:
          - uses: actions/checkout@v3

          - uses: subosito/flutter-action@v2
            with:
              channel: 'stable'
              architecture: x64
          - run: flutter pub get

          - run: pod repo update
            working-directory: ios

          - run: flutter build ios --release --no-codesign

          - run: mkdir Payload
            working-directory: build/ios/iphoneos

          - run: mv Runner.app/ Payload
            working-directory: build/ios/iphoneos

          - name: Zip output
            run: zip -qq -r -9 {ipa_name} Payload
            working-directory: build/ios/iphoneos

          - name: Upload binaries to release
            uses: svenstaro/upload-release-action@v2
            with:
              repo_token: ${{{{ secrets.GITHUB_TOKEN }}}}
              file: build/ios/iphoneos/{ipa_name}
              tag: v1.0
              overwrite: true
              body: "This is first release"
    """
    return textwrap.dedent(yaml_content)

def check_and_install_dependencies(verbose=False):
    check_and_install_git(verbose=verbose)
    check_and_install_gh(verbose=verbose)
    install_python_packages(verbose=verbose)

def main():
    print_ascii_art()
    parser = argparse.ArgumentParser(
        description="Automates the creation and management of GitHub repositories for Flutter iOS projects."
    )
    parser.add_argument(
        '--token', '-t',
        type=str,
        help='Your GitHub Personal Access Token. If not provided, will attempt to read from GITHUB_TOKEN environment variable.'
    )
    parser.add_argument(
        '--action', '-a',
        choices=['createrepo', 'repo'],
        required=True,
        help="Action to perform: 'createrepo' to create a new repository, 'repo' to use an existing repository."
    )
    parser.add_argument(
        '--repo', '-r',
        type=str,
        required=True,
        help='The name of the GitHub repository.'
    )
    parser.add_argument(
        '--ipa-name',
        type=str,
        default='FlutterIpaExport.ipa',
        help='Name of the IPA file to be generated (default: "FlutterIpaExport.ipa").'
    )
    parser.add_argument(
        '--build-dir',
        type=str,
        default='builds',
        help='Directory to store builds (default: "builds").'
    )
    parser.add_argument(
        '--skip-dependencies',
        action='store_true',
        help='Skip checking and installing dependencies.'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip triggering the build and downloading the IPA.'
    )
    parser.add_argument(
        '--skip-upload',
        action='store_true',
        help='Skip uploading the project to GitHub.'
    )
    parser.add_argument(
        '--build-timeout',
        type=int,
        default=30*60,
        help='Build timeout in seconds (default: 1800).'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=30,
        help='Polling interval in seconds (default: 30).'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output.'
    )

    args = parser.parse_args()

    BUILD_TIMEOUT = args.build_timeout
    POLL_INTERVAL = args.poll_interval
    BUILD_DIR = args.build_dir
    IPA_NAME = args.ipa_name

    github_token = get_github_token(args)

    if not args.skip_dependencies:
        check_and_install_dependencies(verbose=args.verbose)
    else:
        print("Skipping dependency checks.")

    repo_name = args.repo
    action = args.action

    if action == "createrepo":
        repo = create_repo(repo_name, github_token, verbose=args.verbose)
        set_workflow_permissions(repo_name, github_token, verbose=args.verbose)
        if not args.skip_upload:
            upload_project(repo_name, github_token, verbose=args.verbose)
        else:
            print("Skipping project upload.")
    elif action == "repo":
        from github import Github, GithubException

        # Check if the repository exists
        g = Github(github_token)
        user = g.get_user()
        try:
            repo = g.get_repo(f"{user.login}/{repo_name}")
            print(f"Repository '{repo_name}' found.")
            set_workflow_permissions(repo_name, github_token, verbose=args.verbose)
        except GithubException:
            print(f"Repository '{repo_name}' was not found. Please ensure the name is correct.")
            sys.exit(1)
        if not args.skip_upload:
            upload_project(repo_name, github_token, verbose=args.verbose)
        else:
            print("Skipping project upload.")

    # Add GitHub Actions Workflow
    workflow_yaml = get_workflow_yaml(IPA_NAME)
    add_github_actions_workflow(workflow_yaml, verbose=args.verbose)

    if not args.skip_build:
        # Trigger the Build
        trigger_workflow_dispatch(repo_name, github_token, verbose=args.verbose)

        # Wait for Build Completion
        wait_for_workflow_completion(repo, github_token, BUILD_TIMEOUT, POLL_INTERVAL, verbose=args.verbose)

        # Download the IPA
        download_ipa(repo, BUILD_DIR, IPA_NAME, verbose=args.verbose)
    else:
        print("Skipping build and download steps.")

if __name__ == "__main__":
    main()
