from anthropic import Anthropic
import os
from dotenv import load_dotenv
import subprocess
import json

load_dotenv()

anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# Takes in a filepath and an a11y issue and returns a suggested fix
def suggest_a11y_fix(filepath: str, a11y_issue: str):

    with open(filepath, "r") as f:
        rawfile = f.read().strip()

    process = subprocess.run(
        ["npx", "prettier", "--stdin-filepath", filepath],
        input=rawfile.encode("utf-8"),
        capture_output=True,
        check=True,
    )

    formatted_file = process.stdout.decode("utf-8")

    TASK_CONTEXT = f"""
    You will be acting as a senior software engineer with professional-level expertise in front-end web
    component a11y. You stay up to date with the latest WCAG a11y standards and best
    practices. You will be given the *contents* of a front-end component file (read from a file path)
    along with a specific a11y issue that was detected on a particular line of code.

    Your job is to:
    1. Analyze the issue and explain why it is problematic.
    2. Suggest a minimal, correct fix that resolves the issue without breaking existing functionality.
    3. Return the full, corrected file and an explanation of your reasoning.

    Always ensure the fix you suggest completely addresses the issue while preserving the original code’s intent
    and functionality.
    """

    TASK_DESCRIPTION = f"""
    Here are some important rules for the interaction:
    - Always stay in character as a senior software engineer.
    - If you are not 100% sure on how to address an a11y issue, say "Sorry, I am unable to confidently
      address this issue." and explain why you are unsure.
    - The input you receive will *always* be wrapped in <input></input> tags. The input will be structured with
      <file></file> and <issue></issue> tags.
    - The <file></file> block will already be nicely formatted with proper indentation and spacing, similar to the examples.
    - You should only modify the code inside the <file> block, based on the issue described in the <issue> block.
    - Never invent new issues or modify unrelated parts of the code.

    **Important for form controls:**
    - For jsx-a11y/control-has-associated-label issues, prefer these patterns:
    1. Nested labels: <label>Label text <input /></label>
    2. aria-label: <input aria-label="Label text" />
    - Avoid using htmlFor/id pattern as it's not recognized by the linter
    
    **Important for images:**
    - Never use words like "image", "photo", or "picture" in alt text - screen readers already announce the element type
    """

    EXAMPLES = r"""
    Here are examples of how to fix common a11y issues:
    <example>
        <input>
            <file>
                const TestComponent = () => {
                    return (
                        <div>
                            <input type="text" />
                        </div>
                    );
                };

                export default TestComponent;
            </file>

            <issue>
            4:7  error  A control must be associated with a text label  jsx-a11y/control-has-associated-label
            </issue>
        </input>

        <response>
            <explanation>
            The input element lacks an accessible label. I've added an aria-label attribute which provides
            a text alternative that screen readers can announce, satisfying the accessibility requirement.
            </explanation>

            <file>
                const TestComponent = () => {
                    return (
                        <div>
                            <input type="text" aria-label="Text input" />
                        </div>
                    );
                };

                export default TestComponent;
            </file>
        </response>
    </example>

    <example>
        <input>
            <file>
                const TestComponent = () => {
                    return (
                        <div>
                            <img src="logo.png" />
                        </div>
                    );
                };

                export default TestComponent;
            </file>

            <issue>
            4:7  error  img elements must have an alt prop, either with meaningful text, or an empty string for decorative images  jsx-a11y/alt-text
            </issue>
        </input>

        <response>
            <explanation>
            The img element lacks an alt attribute. I've added an alt attribute with a meaningful description of the image.
            </explanation>

            <file>
                const TestComponent = () => {
                    return (
                        <div>
                            <img src="logo.png" alt="Company logo" />
                        </div>
                    );
                };

                export default TestComponent;
            </file>
        </response>
    </example>

    <example>
        <input>
            <file>
                const TestComponent = () => {
                    const handleClick = () => console.log('clicked');
                    return (
                        <div>
                            <div onClick={handleClick}>Click me</div>
                        </div>
                    );
                };

                export default TestComponent;
            </file>

            <issue>
            5:7  error  Visible, non-interactive elements with click handlers must have at least one keyboard listener.  jsx-a11y/click-events-have-key-events
            5:7  error  Avoid non-native interactive elements. If using native HTML is not possible, add an appropriate role and support for tabbing, mouse, keyboard, and touch inputs to an interactive content element.  jsx-a11y/no-static-element-interactions
            </issue>
        </input>

        <response>
            <explanation>
            The div element is being used as an interactive element but lacks proper keyboard support and semantic meaning. 
            I've replaced it with a button element, which provides built-in keyboard navigation, focus management, 
            and is automatically recognized as interactive by screen readers.
            </explanation>

            <file>
                const TestComponent = () => {
                    const handleClick = () => console.log('clicked');
                    return (
                    <div>
                        <button onClick={handleClick}>Click me</button>
                    </div>
                );
            };

            export default TestComponent;
            </file>
        </response>
    </example>
    """

    OUTPUT_FORMATTING = f"""
    Put your entire response in <response></response> tags. Similar to the example, wrap your explanation in
    <explanation></explanation> tags, and wrap your newly suggested file in <file></file> tags.
    """

    prompt = f"{TASK_CONTEXT}\n{TASK_DESCRIPTION}\n{EXAMPLES}\n{OUTPUT_FORMATTING}\n\n<input>\n<file>{formatted_file}</file>\n<issue>{a11y_issue}</issue>\n</input>"

    messages = [
        {"role": "user", "content": prompt},
    ]

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        temperature=0.2,
        messages=messages,
    )

    return response.content[0].text


# Takes in a filepath and returns a list of a11y issues from linter
def get_a11y_issues(filepath: str):
    """
    Takes in a JS/JSX file path and returns a list of accessibility issues
    detected by ESLint, plus the formatted file.

    Returns:
        issues (list[str]): List of formatted issue strings
        formatted_file (str): Prettier-formatted file contents
    """
    try:
        # Format the file with Prettier first
        with open(filepath, "r") as f:
            rawfile = f.read().strip()

        prettier_process = subprocess.run(
            ["npx", "prettier", "--stdin-filepath", filepath],
            input=rawfile.encode("utf-8"),
            capture_output=True,
            check=True,
        )
        formatted_file = prettier_process.stdout.decode("utf-8")

        # Run ESLint directly on file
        eslint_process = subprocess.run(
            ["npx", "eslint", filepath, "-f", "json"],
            capture_output=True,
            text=True,
            check=False,
        )

        # Parse ESLint JSON output
        issues = []
        if eslint_process.stdout:
            eslint_results = json.loads(eslint_process.stdout)

            # Extract issues from the first file
            if eslint_results and len(eslint_results) > 0:
                file_result = eslint_results[0]
                messages = file_result.get("messages", [])

                # Filter for a11y issues and format them
                for msg in messages:
                    if msg.get("ruleId", "").startswith("jsx-a11y/"):
                        # Format like ESLint's normal output
                        issue_str = f"{msg['line']}:{msg['column']}  error  {msg['message']}  {msg['ruleId']}"
                        issues.append(issue_str)

                print(f"Found {len(issues)} a11y issues \n")

        return issues, formatted_file

    except Exception as e:
        print(f"Error: {e}")
        return [], ""
