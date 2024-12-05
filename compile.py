import sys
import subprocess
import time
import platform
import argparse
import shutil
import os
import textwrap

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

def run_command(command, cwd=None, capture_output=True, verbose=False):
    if verbose:
        print(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True
        )
        if capture_output and verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        return result.stdout if capture_output else None
    except subprocess.CalledProcessError as e:
        if capture_output:
            print(f"Error executing: {command}\n{e.stderr}")
        else:
            print(f"Error executing: {command}")
        sys.exit(1)

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
        auth_status = run_command("gh auth status", capture_output=True, verbose=verbose)
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
    from github import Github, GithubException

    # Initialize Git repository if not already done
    if not os.path.isdir(".git"):
        print("Initializing Git repository...")
        run_command("git init", capture_output=False, verbose=verbose)

    # Set remote 'origin' if not already set
    remotes = run_command("git remote", capture_output=True, verbose=verbose)
    if "origin" not in remotes:
        github_username = get_github_username(github_token)
        remote_url = f"https://github.com/{github_username}/{repo_name}.git"
        print(f"Setting remote 'origin' to {remote_url}")
        run_command(f"git remote add origin {remote_url}", capture_output=False, verbose=verbose)
    else:
        print("Remote 'origin' is already set.")

    # Add files and push
    print("Adding files to Git...")
    run_command("git add .", capture_output=False, verbose=verbose)
    commit_message = "Initial commit"
    run_command(f'git commit -m "{commit_message}"', capture_output=False, verbose=verbose)
    print("Pushing files to GitHub...")
    run_command("git branch -M main", capture_output=False, verbose=verbose)
    run_command("git push -u origin main", capture_output=False, verbose=verbose)
    print(f"Project successfully uploaded to repository '{repo_name}'.")

def get_github_username(github_token):
    from github import Github

    g = Github(github_token)
    user = g.get_user()
    return user.login

def add_github_actions_workflow(repo, workflow_content, verbose=False):
    from github import GithubException

    try:
        repo.create_file(
            ".github/workflows/build_ios.yml",
            "Add GitHub Actions workflow for iOS build",
            workflow_content
        )
        print("GitHub Actions workflow file successfully added.")
    except GithubException as e:
        if e.data['message'] == 'Invalid request.\n\n"sha" was not supplied.':
            print("Workflow file already exists. Updating the existing file.")
            contents = repo.get_contents(".github/workflows/build_ios.yml")
            repo.update_file(
                contents.path,
                "Update GitHub Actions workflow for iOS build",
                workflow_content,
                contents.sha
            )
            print("GitHub Actions workflow file successfully updated.")
        else:
            print(f"Error adding the workflow file: {e.data['message']}")
            sys.exit(1)

def trigger_build(repo_name, github_token, verbose=False):
    print("Triggering GitHub Actions workflow through a dummy commit...")
    dummy_file = "trigger_build.txt"
    with open(dummy_file, "w") as f:
        f.write(f"Trigger build at {time.ctime()}\n")
    run_command(f"git add {dummy_file}", capture_output=False, verbose=verbose)
    run_command('git commit -m "Trigger GitHub Actions build"', capture_output=False, verbose=verbose)
    run_command("git push", capture_output=False, verbose=verbose)
    print("Dummy commit successfully pushed; GitHub Actions workflow should now be running.")

def wait_for_workflow_completion(repo, github_token, build_timeout, poll_interval, verbose=False):
    from github import Github

    g = Github(github_token)
    user = g.get_user()
    repository = g.get_repo(f"{user.login}/{repo.name}")
    workflows = repository.get_workflows()
    if workflows.totalCount == 0:
        print("No workflows found.")
        sys.exit(1)
    workflow = workflows[0]
    print("Waiting for the GitHub Actions workflow to complete...")
    start_time = time.time()
    while time.time() - start_time < build_timeout:
        runs = workflow.get_runs(status="in_progress")
        if runs.totalCount == 0:
            # Check for the latest run
            latest_run = workflow.get_runs().reversed[0]
            if latest_run.conclusion == "success":
                print("GitHub Actions workflow completed successfully.")
                return
            elif latest_run.conclusion is not None:
                print(f"GitHub Actions workflow failed with conclusion: {latest_run.conclusion}")
                sys.exit(1)
        else:
            print("Workflow is still running... Waiting.")
            time.sleep(poll_interval)
    print("Timeout reached. The GitHub Actions workflow did not complete within the expected time.")
    sys.exit(1)

def download_ipa(repo, builds_dir, verbose=False):
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
    ipa_path = os.path.join(builds_dir, ipa_asset.name)
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

def get_workflow_yaml():
    yaml_content = """
    name: iOS-ipa-build

    on:
      workflow_dispatch:

    jobs:
      build-ios:
        name: 🎉 iOS Build
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
            run: zip -qq -r -9 FlutterIpaExport.ipa Payload
            working-directory: build/ios/iphoneos

          - name: Upload binaries to release
            uses: svenstaro/upload-release-action@v2
            with:
              repo_token: ${{ secrets.GITHUB_TOKEN }}
              file: build/ios/iphoneos/FlutterIpaExport.ipa
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
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output.'
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

    args = parser.parse_args()

    BUILD_TIMEOUT = args.build_timeout
    POLL_INTERVAL = args.poll_interval
    BUILD_DIR = args.build_dir

    github_token = get_github_token(args)

    if not args.skip_dependencies:
        check_and_install_dependencies(verbose=args.verbose)
    else:
        print("Skipping dependency checks.")

    repo_name = args.repo
    action = args.action

    if action == "createrepo":
        repo = create_repo(repo_name, github_token, verbose=args.verbose)
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
        except GithubException:
            print(f"Repository '{repo_name}' was not found. Please ensure the name is correct.")
            sys.exit(1)
        if not args.skip_upload:
            upload_project(repo_name, github_token, verbose=args.verbose)
        else:
            print("Skipping project upload.")

    if not args.skip_build:
        # Add GitHub Actions Workflow
        workflow_yaml = get_workflow_yaml()
        add_github_actions_workflow(repo, workflow_yaml, verbose=args.verbose)

        # Trigger the Build
        trigger_build(repo_name, github_token, verbose=args.verbose)

        # Wait for Build Completion
        wait_for_workflow_completion(repo, github_token, BUILD_TIMEOUT, POLL_INTERVAL, verbose=args.verbose)

        # Download the IPA
        download_ipa(repo, BUILD_DIR, verbose=args.verbose)
    else:
        print("Skipping build and download steps.")

if __name__ == "__main__":
    main()