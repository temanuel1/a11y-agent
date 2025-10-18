from tools import get_a11y_issues, suggest_a11y_fixes
import difflib


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
    Fully automated a11y pipeline that directly updates the input file.
    """
    with open(file_path, "r") as f:
        original_content = f.read()

    # Make a backup before any changes
    backup_path = file_path.replace(".tsx", "_old.tsx").replace(".jsx", "_old.jsx")
    with open(backup_path, "w") as f:
        f.write(original_content)

    last_content = original_content  # Track last version

    round_num = 1
    while round_num <= max_rounds:
        print(f"\nRound {round_num}")

        issues, formatted_file = get_a11y_issues(file_path)
        if not issues:
            print("No more a11y issues found! File is clean.")
            break

        print(f"Found {len(issues)} a11y issues.")
        with open(file_path, "w") as f:
            f.write(formatted_file)

        fix_response = suggest_a11y_fixes(file_path, issues)
        fixed_content = extract_tag_content(fix_response, "file")

        if not fixed_content:
            print("No <file> block found in model response. Stopping.")
            break

        # Stop if no actual change occurred
        if not files_are_different(last_content, fixed_content):
            print("Model did not produce any new changes. Stopping to avoid infinite loop.")
            break

        with open(file_path, "w") as f:
            f.write(fixed_content.strip() + "\n")

        explanation = extract_tag_content(fix_response, "explanation")
        if explanation:
            print(f"\nFix explanation:\n{explanation}\n")

        # Update for next round
        last_content = fixed_content
        round_num += 1

    if round_num > max_rounds:
        print("Reached maximum number of rounds. Some issues may remain.")


if __name__ == "__main__":
    run("./test.tsx")
