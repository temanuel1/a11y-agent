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

    Use the group_issues tool to return your grouping.
    """

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
        tools=[
            {
                "name": "group_issues",
                "description": "Group related accessibility issues that should be fixed together",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "groups": {
                            "type": "array",
                            "description": "Array of issue groups, where each group is an array of issue numbers",
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "integer",
                                    "description": "Issue number (1-indexed)"
                                }
                            }
                        }
                    },
                    "required": ["groups"]
                }
            }
        ],
        tool_choice={"type": "tool", "name": "group_issues"}
    )
    
    try:
        tool_use = next(block for block in response.content if block.type == "tool_use")
        groupings = tool_use.input["groups"]
        
        grouped_issues = []
        for group in groupings:
            issue_group = [issues[i-1] for i in group]
            grouped_issues.append(issue_group)
        
        return grouped_issues
        
    except Exception as e:
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
    with open(file_path, "r") as f:
        original_content = f.read()
    backup_path = file_path.replace(".tsx", "_old.tsx").replace(".jsx", "_old.jsx")
    with open(backup_path, "w") as f:
        f.write(original_content)

    issues, formatted_file = get_a11y_issues(file_path)

    if not issues:
        return formatted_file

    with open(file_path, "w") as f:
        f.write(formatted_file)

    issue_groups = group_issues_intelligently(issues, file_path)
    
    for i, issue_group in enumerate(issue_groups):
        combined_issues = "\n".join(issue_group)
        
        fix_response = suggest_a11y_fix(file_path, combined_issues)

        fixed_content = extract_tag_content(fix_response, "file")
        
        if fixed_content:
            with open(file_path, "w") as f:
                f.write(fixed_content)
            
            explanation = extract_tag_content(fix_response, "explanation")
            if explanation:
                print(f"\n{explanation}")


if __name__ == "__main__":
    run("./test.tsx")