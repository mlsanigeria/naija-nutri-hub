# update_leaderboard.py
# This script updates the GitHub Leaderboard in the README.md file
import requests
from collections import defaultdict
import os

print("Updating the GitHub Leaderboard...")

def initialize_api():
    # Define your GitHub repository and authentication token
    repository_owner = "mlsanigeria"
    repository_name = "naija-nutri-hub"
    api_token = os.environ.get("API_TOKEN")

    # Define the GitHub API endpoint for pull requests
    api_url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/pulls"

    # Define query parameters to filter pull requests (only closed ones)
    params = {
        "state": "closed",
        "sort": "updated",
        "direction": "desc",
        'per_page': 100,  # Number of PRs per page (max is typically 100)
        'page': 1,  # Start with page 1
    }

    # Add your GitHub token to the request headers for authentication
    headers = {
        "Authorization": f"Bearer {api_token}",
    }

    all_prs = []
    while True:
        print(f"Fetching PRs, page: {params['page']}")  # Debug: print current page number
        response = requests.get(api_url, params=params, headers=headers)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            pull_requests = response.json()
            print(f"Fetched {len(pull_requests)} PRs")  # Debug: number of PRs fetched

            if not pull_requests:
                print("No more PRs to fetch. Exiting loop.")  # Debug: No more PRs
                break
            else:
                # Extend the list of all PRs with the current page's PRs
                all_prs.extend(pull_requests)
                # Move to the next page
                params['page'] += 1
        else:
            print(f"Error fetching PRs: {response.status_code}")  # Debug: print error code
            break

    print(f"Total PRs fetched: {len(all_prs)}")  # Debug: total PRs fetched
    return all_prs


def get_sorted_pr():
    print("Fetching and sorting pull requests...")  # Debug: process start message
    response = initialize_api()
    
    # Create a dictionary to track the count of merged pull requests by each user
    merged_prs_count_by_user = defaultdict(int)
    avi = {}
    # Create a list of contributors to exempt
    exempt = ["Sammybams"] # "Odeyiany2"

    # Iterate through the pull_requests list
    for pr in response:
        # Check if the pull request was merged and get the username of the user who merged it
        if pr['merged_at']:
            pr_by = pr['user']['login']
            
            # Check if the user is exempted
            if pr_by in exempt:
                print(f"Skipping exempt user: {pr_by}")  # Debug: Skipping user
                continue
            else:
                # Increment the count of merged pull requests for this user
                merged_prs_count_by_user[pr_by] += 1
                avi[pr_by] = pr['user']['avatar_url']
                print(f"User: {pr_by}, Merged PRs: {merged_prs_count_by_user[pr_by]}")  # Debug: user PR count

    # Sort the users by the number of merged pull requests in descending order
    sorted_users = sorted(merged_prs_count_by_user.items(), key=lambda x: (-x[1], x[0].lower()))
    print(f"Total contributors: {len(sorted_users)}")  # Debug: total contributors count
    return sorted_users, avi

def leaderboard_data():
    print("Generating leaderboard data...")  # Debug: process start message
    sorted_users, avi = get_sorted_pr()
    leaderboard_data = []
    rank = 1
    last_count = 0
    pos = 1

    # Dictionary to store medals
    medals = {
        1: "🥇",  # Gold Medal
        2: "🥈",  # Silver Medal
        3: "🥉",  # Bronze Medal
    }

    for user, count in sorted_users:
        if count == last_count:
            rank -= 1
            leaderboard_data.append({"position": pos, "rank":medals.get(rank,rank), "avi": f"<img src='{avi[user]}' alt='Avatar' width='30' height='30'>", "contributor": f"[{user}](https://github.com/{user})", "merged_prs": f"{count}"})
        else:
            last_count = count
            leaderboard_data.append({"position": pos, "rank":medals.get(rank,rank), "avi": f"<img src='{avi[user]}' alt='Avatar' width='30' height='30'>", "contributor": f"[{user}](https://github.com/{user})", "merged_prs": f"{count}"})
        rank += 1
        pos += 1

    print(f"Generated leaderboard data for {len(leaderboard_data)} contributors.")  # Debug: leaderboard count
    return leaderboard_data


leaderboard_data = leaderboard_data()

# Generate the Markdown content for the leaderboard
leaderboard_content = """
# GitHub Leaderboard

🏆 **Welcome to the Official Leaderboard!** 🏆

Celebrate the remarkable contributions of our top contributors.

| S/N | Rank || Contributor | Merged PRs |
|--| ---- | -- |----------- | ---------- |
{}

A heartfelt **thank you** to all our fantastic contributors for their hard work and dedication! Together, we're making a difference in the open-source community.

---

*Want to see your name on the leaderboard? Contribute to our project on [GitHub](https://github.com/mlsanigeria/speak-to-docs) and make an impact!*

""".format("\n".join(
    f"| {entry['position']} | {entry['rank']} | {entry['avi']} | {entry['contributor']} | {entry['merged_prs']} |"
    for entry in leaderboard_data
))

# Write the Markdown content to LEADERBOARD.md
with open("LEADERBOARD.md", "w") as readme_file:
    readme_file.write(leaderboard_content)
    print("Successfully updated LEADERBOARD.md")  # Debug: Success message


# Filter only the top 10 contributors
max_position = 10
filtered_data = [contributor for contributor in leaderboard_data if contributor['position'] <= max_position]
print(f"Filtered top {max_position} contributors.")  # Debug: Filtered top contributors

# Generate the Markdown content for the README
readme_content = """
### Top 10 Contributors

Thank you to all our fantastic contributors for their hard work and dedication! Here are our top 10 contributors:

| S/N | Rank || Contributor | Merged PRs |
|--| ---- | -- |----------- | ---------- |
{}

Thank you to all our fantastic contributors for their hard work and dedication!

""".format("\n".join(
    f"| {entry['position']} | {entry['rank']} | {entry['avi']} | {entry['contributor']} | {entry['merged_prs']} |"
    for entry in filtered_data
))

def update_readme_section(readme_path, section_start, section_end, new_content):
    """
    Update a specific section within a file without replacing section markers.

    Args:
        readme_path (str): The path to the README file.
        section_start (str): The start marker for the section to be updated.
        section_end (str): The end marker for the section to be updated.
        new_content (str): The new content to insert into the section.

    Returns:
        bool: True if the section was successfully updated, False otherwise.
    """
    try:
        print(f"Updating README section from {section_start} to {section_end}")  # Debug: update message
        # Open and read the README file
        with open(readme_path, 'r') as file:
            readme_contents = file.read()

        # Locate the section to update
        section_start_index = readme_contents.find(section_start)
        section_end_index = readme_contents.find(section_end)

        if section_start_index == -1 or section_end_index == -1 or section_start_index >= section_end_index:
            # Section not found or invalid markers, return False
            print("Section markers not found or invalid.")  # Debug: Section not found
            return False

        # Update the section content
        updated_section = section_start + new_content + section_end
        updated_readme_contents = (
            readme_contents[:section_start_index] +
            updated_section +
            readme_contents[section_end_index + len(section_end):]
        )

        # Write the updated contents back to the file
        with open(readme_path, 'w') as file:
            file.write(updated_readme_contents)
        print("Section updated successfully.")  # Debug: Section updated
        return True  # Section updated successfully

    except Exception as e:
        print(f"An error occurred: {e}")  # Debug: Exception message
        return False

readme_path = 'README.md'
section_start = "<!-- Section Start -->"
section_end = "<!-- Section End -->"
new_content = readme_content

if update_readme_section(readme_path, section_start, section_end, new_content):
    print("README section updated successfully.")
else:
    print
