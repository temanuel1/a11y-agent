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
    print(f"Created backup at: {backup_path}")

    last_content = original_content

    # Phase 1: Fix Static Issues First
    print("\n" + "="*60)
    print("PHASE 1: STATIC ANALYSIS (ESLint)")
    print("="*60)
    
    round_num = 1
    while round_num <= max_rounds:
        print(f"\nStatic Round {round_num}")

        issues, formatted_file = get_a11y_issues(file_path)
        if not issues:
            print("✓ Static issues clean!")
            break

        print(f"Found {len(issues)} static issue(s).")
        with open(file_path, "w") as f:
            f.write(formatted_file)

        fix_response = suggest_a11y_fixes(file_path, issues)
        fixed_content = extract_tag_content(fix_response, "file")

        if not fixed_content:
            print("Error: No <file> block found. Stopping.")
            break

        if not files_are_different(last_content, fixed_content):
            print("No changes made. Stopping.")
            break

        with open(file_path, "w") as f:
            f.write(fixed_content.strip() + "\n")

        last_content = fixed_content
        round_num += 1

    if round_num > max_rounds:
        print(f"Reached max static analysis rounds ({max_rounds}). Moving to runtime analysis.")

    # Copy to server template
    print("\n" + "="*60)
    print("COPYING TO SERVER TEMPLATE")
    print("="*60)
    server_template_path = os.path.join("../server/template", os.path.basename(file_path))
    shutil.copy(file_path, server_template_path)
    print(f"Copied {file_path} → {server_template_path}")

    # Phase 2: Combined Verification (check BOTH until clean)
    print("\n" + "="*60)
    print("PHASE 2: COMBINED VERIFICATION (ESLint + Lighthouse)")
    print("="*60)
    
    round_num = 1
    issue_history = []

    while round_num <= max_rounds:
        print(f"\nCombined Round {round_num}")

        # Check BOTH sources
        static_issues, _ = get_a11y_issues(file_path)
        runtime_issues = get_lighthouse_issues(file_path)
        all_issues = static_issues + runtime_issues

        if not all_issues:
            print("All checks passed, component is fully accessible")
            break

        # DEADLOCK DETECTION: Check if same issue types keep repeating
        if round_num >= 3:
            # Extract rule names from issues (last part after splitting)
            current_rules = set(issue.split()[-1] for issue in all_issues)
            
            # Check if we've seen these exact rules in the last 2 rounds
            if len(issue_history) >= 2:
                past_rules_1 = set(issue.split()[-1] for issue in issue_history[-1])
                past_rules_2 = set(issue.split()[-1] for issue in issue_history[-2])
                
                if current_rules == past_rules_1 and current_rules == past_rules_2:
                    print(f"\nDEADLOCK DETECTED!")
                    print(f"Same {len(current_rules)} issue type(s) repeating for 3 rounds:")
                    for rule in current_rules:
                        print(f"  - {rule}")
                    print("\nThese issues may be false positives or incorrectly mapped.")
                    print("Visual inspection recommended. Stopping to prevent infinite loop.\n")
                    break

        issue_history.append(all_issues.copy())

        print(f"Found {len(static_issues)} static + {len(runtime_issues)} runtime = {len(all_issues)} total issue(s).")

        # Fix ALL issues together
        fix_response = suggest_a11y_fixes(file_path, all_issues)
        fixed_content = extract_tag_content(fix_response, "file")

        if not fixed_content:
            print("Error: No <file> block found. Stopping.")
            break

        if not files_are_different(last_content, fixed_content):
            print("No changes made. Stopping.")
            break

        with open(file_path, "w") as f:
            f.write(fixed_content.strip() + "\n")
        
        # Update server template
        shutil.copy(file_path, server_template_path)

        last_content = fixed_content
        round_num += 1

    if round_num > max_rounds:
        print(f"\nReached max combined rounds ({max_rounds}).")
        print("Some issues may remain. Manual review recommended.")

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"Final file: {file_path}")
    print(f"Backup: {backup_path}")
    print(f"\nTip: To visually verify, run:")
    print(f"   cd ../server/template && npx vite")
    print(f"   Then visit http://localhost:5173")


if __name__ == "__main__":
    run("./test.tsx")