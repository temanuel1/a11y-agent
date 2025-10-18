from tools import get_a11y_issues, suggest_a11y_fixes, get_lighthouse_issues
import shutil
import difflib
import os


def extract_tag_content(text, tag):
    """Extract content between XML tags."""
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    if start_tag in text and end_tag in text:
        return text.split(start_tag)[1].split(end_tag)[0].strip()
    return None


def files_are_different(old_content: str, new_content: str) -> bool:
    """Check if the model's fix actually changed the file."""
    diff = list(difflib.unified_diff(
        old_content.splitlines(),
        new_content.splitlines(),
        lineterm=""
    ))
    return len(diff) > 0


def run(file_path: str, max_rounds: int = 5):
    """
    Fully automated a11y pipeline: static first, then combined verification.
    """
    with open(file_path, "r") as f:
        original_content = f.read()

    backup_path = os.path.join("../.backups", os.path.basename(file_path).replace(".tsx", "_old.tsx"))
    os.makedirs("../.backups", exist_ok=True)
    
    with open(backup_path, "w") as f:
        f.write(original_content)
    print(f"created backup at: {backup_path}")

    last_content = original_content

    # phase 1: static analysis (eslint)
    print("phase 1: static analysis (eslint)")
    
    round_num = 1
    while round_num <= max_rounds:
        print(f"\nstatic round {round_num}")

        issues, formatted_file = get_a11y_issues(file_path)
        if not issues:
            print("static issues clean")
            break

        print(f"found {len(issues)} static issue(s)")
        with open(file_path, "w") as f:
            f.write(formatted_file)

        fix_response = suggest_a11y_fixes(file_path, issues)
        fixed_content = extract_tag_content(fix_response, "file")

        if not fixed_content:
            print("error: no <file> block found. stopping.")
            break

        if not files_are_different(last_content, fixed_content):
            print("no changes made. stopping.")
            break

        with open(file_path, "w") as f:
            f.write(fixed_content.strip() + "\n")

        last_content = fixed_content
        round_num += 1

    if round_num > max_rounds:
        print(f"reached max static analysis rounds ({max_rounds}). moving to runtime analysis.")

    # copy to server template
    print("copying to server template")
    server_template_path = os.path.join("../server/template", os.path.basename(file_path))
    shutil.copy(file_path, server_template_path)
    print(f"copied {file_path} → {server_template_path}")

    # phase 2: combined verification (eslint + lighthouse)
    print("phase 2: combined verification (eslint + lighthouse)")
    
    round_num = 1
    issue_history = []

    while round_num <= max_rounds:
        print(f"\ncombined round {round_num}")

        # check both sources
        static_issues, _ = get_a11y_issues(file_path)
        runtime_issues = get_lighthouse_issues(file_path)
        all_issues = static_issues + runtime_issues

        if not all_issues:
            print("all checks passed, component is fully accessible")
            break

        # deadlock detection: check if same issue types keep repeating
        if round_num >= 3:
            # extract rule names from issues (last part after splitting)
            current_rules = set(issue.split()[-1] for issue in all_issues)
            
            # Check if we've seen these exact rules in the last 2 rounds
            if len(issue_history) >= 2:
                past_rules_1 = set(issue.split()[-1] for issue in issue_history[-1])
                past_rules_2 = set(issue.split()[-1] for issue in issue_history[-2])
                
                if current_rules == past_rules_1 and current_rules == past_rules_2:
                    print(f"\n[debug] deadlock detected!")
                    print(f"same {len(current_rules)} issue type(s) repeating for 3 rounds:")
                    for rule in current_rules:
                        print(f"  - {rule}")
                    print("\nthese issues may be false positives or incorrectly mapped.")
                    print("visual inspection recommended. stopping to prevent infinite loop.\n")
                    break

        issue_history.append(all_issues.copy())

        print(f"found {len(static_issues)} static + {len(runtime_issues)} runtime = {len(all_issues)} total issue(s)")

        # fix all issues together
        fix_response = suggest_a11y_fixes(file_path, all_issues)
        fixed_content = extract_tag_content(fix_response, "file")

        if not fixed_content:
            print("error: no <file> block found. stopping.")
            break

        if not files_are_different(last_content, fixed_content):
            print("no changes made. stopping.")
            break

        with open(file_path, "w") as f:
            f.write(fixed_content.strip() + "\n")
        
        # update server template
        shutil.copy(file_path, server_template_path)

        last_content = fixed_content
        round_num += 1

    if round_num > max_rounds:
        print(f"\nreached max combined rounds ({max_rounds}).")
        print("some issues may remain. manual review recommended.")

    print(f"final file: {file_path}")
    print(f"backup: {backup_path}")
    print(f"\ntip: to visually verify, run:")
    print(f"   cd ../server/template && npx vite")
    print(f"   Then visit http://localhost:5173")


if __name__ == "__main__":
    run("./test.tsx")