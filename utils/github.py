import os
from github import Github, GithubException
from utils.logging_config import logger, log_error
import yaml

def create_yaml_content(detection_name, description, detection_rule):
    # Ensure multi-line strings are properly formatted for YAML
    def format_multiline(text):
        return '|\n' + '\n'.join(f'  {line}' for line in text.split('\n'))

    yaml_content = f"""
# Detection Name: {detection_name}

description: {format_multiline(description)}

detection_rule: {format_multiline(detection_rule)}

tags:
  - auto-generated
  - DIANA
"""
    return yaml_content

def sync_to_github(detection_name, detection_rule, description):
    logger.info(f"Starting GitHub sync for detection: {detection_name}")
    try:
        github_token = os.getenv('GITHUB_TOKEN')
        repo_name = os.getenv('GITHUB_REPO')
        if not github_token or not repo_name:
            logger.error("GitHub token or repository name not found in environment variables")
            return False, "GitHub configuration is incomplete"

        g = Github(github_token)
        repo = g.get_repo(repo_name)
        main_branch = repo.get_branch("main")

        file_path = f"detections/{detection_name.replace(' ', '_')}.yml"
        
        yaml_content = create_yaml_content(detection_name, description, detection_rule)

        try:
            # Check if the file exists in the main branch
            existing_file = repo.get_contents(file_path, ref=main_branch.commit.sha)
            
            # File exists, update it in the main branch
            logger.info(f"Updating existing file in main branch: {file_path}")
            repo.update_file(
                file_path,
                f"Update detection: {detection_name}",
                yaml_content,
                existing_file.sha,
                branch="main"
            )
            logger.info(f"Successfully updated file in main branch: {file_path}")
            return True, f"Updated existing detection {detection_name} in main branch"
            
        except GithubException as e:
            if e.status == 404:
                # File doesn't exist, create a new branch and add the file
                new_branch_name = f"new-detection-{detection_name.replace(' ', '-').lower()}"
                logger.info(f"Creating new branch: {new_branch_name}")
                
                # Create a new branch from main
                new_branch_ref = f"refs/heads/{new_branch_name}"
                repo.create_git_ref(new_branch_ref, main_branch.commit.sha)
                
                # Create the new file in the new branch
                logger.info(f"Creating new file in branch {new_branch_name}: {file_path}")
                repo.create_file(
                    file_path,
                    f"Add new detection: {detection_name}",
                    yaml_content,
                    branch=new_branch_name
                )
                
                # Create a pull request
                pr = repo.create_pull(
                    title=f"Add new detection: {detection_name}",
                    body=f"New detection rule added for {detection_name}",
                    head=new_branch_name,
                    base="main"
                )
                logger.info(f"Created pull request: {pr.html_url}")
                return True, f"Created new branch and pull request for {detection_name}"
            else:
                raise

    except GithubException as e:
        error_message = f"GitHub API error: {e.status}, {e.data}"
        log_error(error_message)
        return False, error_message
    except Exception as e:
        error_message = f"Error syncing to GitHub: {str(e)}"
        log_error(error_message, exc_info=True)
        return False, error_message

def test_github_connection():
    logger.info("Testing GitHub connection")
    try:
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            logger.error("GitHub token not found in environment variables")
            raise ValueError("GitHub token not found in environment variables")
        
        repo_name = os.getenv('GITHUB_REPO')
        if not repo_name:
            logger.error("GitHub repository name not found in environment variables")
            raise ValueError("GitHub repository name not found in environment variables")
        
        logger.debug(f"Attempting to access repo: {repo_name}")
        
        g = Github(github_token)
        user = g.get_user()
        logger.info(f"Authenticated as GitHub user: {user.login}")
        
        repo = g.get_repo(repo_name)
        logger.info(f"Successfully connected to GitHub repo: {repo.full_name}")
        return repo.full_name
    except GithubException as e:
        log_error(f"GitHub API error: {e.status}, {e.data}")
        raise
    except Exception as e:
        log_error(f"Error testing GitHub connection: {str(e)}", exc_info=True)
        raise