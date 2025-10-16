from anthropic import Anthropic
import os
from dotenv import load_dotenv
from tools import get_a11y_issues, suggest_a11y_fix
import json

load_dotenv()

anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def group_issues_intelligently(issues, file_path):
    """Use LLM to intelligently group related issues that should be fixed together"""
    
    with open(file_path, "r") as f:
        file_content = f.read()
    
    # TODO: Improve prompt (like the one in tools.py)
    prompt = f"""
    You are analyzing accessibility issues in a React component. Your job is to intelligently group related 
    issues that should be fixed together.

    <file>
        {file_content}
    </file>

    <issues>
        {chr(10).join([f"{i+1}. {issue}" for i, issue in enumerate(issues)])}
    </issues>

    Group these issues intelligently based on:
    1. Issues affecting the same element (even if on different lines, like a label and its input)
    2. Issues that are semantically related and should be fixed together
    3. Issues where fixing one might affect or conflict with another

    Return your grouping as a JSON array of arrays, where each inner array contains the issue numbers that should be fixed together.
    For example: [[1, 2], [3], [4, 5]] means issues 1&2 should be fixed together, issue 3 alone, and issues 4&5 together.

    Only return the JSON array, nothing else.
    """

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        response_text = response.content[0].text.strip()
        
        # remove markdown code blocks if present
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        groupings = json.loads(response_text)
        
        # convert issue numbers back to actual issues
        grouped_issues = []
        for group in groupings:
            issue_group = [issues[i-1] for i in group]
            grouped_issues.append(issue_group)
        
        return grouped_issues
        
    except Exception as e:
        # fallback: each issue separately
        return [[issue] for issue in issues]


def extract_tag_content(text, tag):
    """Extract content between XML tags"""
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    if start_tag in text and end_tag in text:
        return text.split(start_tag)[1].split(end_tag)[0].strip()
    return None


def run(file_path: str):
    """
    Fully automated a11y pipeline that directly updates the input file
    """
    # backup original file
    with open(file_path, "r") as f:
        original_content = f.read()
    backup_path = file_path.replace(".tsx", "_old.tsx").replace(".jsx", "_old.jsx")
    with open(backup_path, "w") as f:
        f.write(original_content)

    # get all issues and formatted code
    issues, formatted_file = get_a11y_issues(file_path)

    if not issues:
        return formatted_file

    # write formatted version to file
    with open(file_path, "w") as f:
        f.write(formatted_file)

    # intelligently group related issues
    issue_groups = group_issues_intelligently(issues, file_path)
    
    # fix each group together
    for i, issue_group in enumerate(issue_groups):
        combined_issues = "\n".join(issue_group)
        
        # get fix for current state of the file
        fix_response = suggest_a11y_fix(file_path, combined_issues)

        # extract and apply the fixed content
        fixed_content = extract_tag_content(fix_response, "file")
        
        if fixed_content:
            with open(file_path, "w") as f:
                f.write(fixed_content)
            
            explanation = extract_tag_content(fix_response, "explanation")
            if explanation:
                print(f"\n{explanation}")


run("/Users/tyleremanuel/Documents/Bench/a11y-agent/agent/test.tsx")