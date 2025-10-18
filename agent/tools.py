from anthropic import Anthropic
import os
from dotenv import load_dotenv
import subprocess
import json
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server.server import run_lighthouse_analysis

load_dotenv()

anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# takes in a filepath and an a11y issue and returns a suggested fix
def suggest_a11y_fixes(filepath: str, a11y_issues: list[str]):

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
    along with a list of specific a11y issues that were detected on particular lines of code.

    Your job is to:
    1. Carefully and thoroughly read through all the code and issues.
    2. Determine which issues (if any) can be logically grouped together and fixed together.
    3. For each issue (or issue group), analyze the issues and explain why they are problematic.
    4. Suggest a minimal, correct fix that resolves the issues without breaking existing functionality.
    5. Return the full, corrected file and an explanation of your reasoning.

    Always ensure the fix you suggest completely addresses the issues while preserving the original code's intent
    and functionality.
    """

    TASK_DESCRIPTION = f"""
    Here are some important rules for the interaction:
    - Always stay in character as a senior software engineer.
    - If you are not 100% sure on how to address an a11y issue, say "Sorry, I am unable to confidently
      address this issue." and explain why you are unsure.
    - The input you receive will *always* be wrapped in <input></input> tags. The input will be structured with
      <file></file> and <issues></issues> tags.
    - The <file></file> block will already be nicely formatted with proper indentation and spacing, similar to the examples.
    - You should only modify the code inside the <file> block, based on the issues described in the <issues> block.
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

            <issues>
            ['4:7  error  A control must be associated with a text label  jsx-a11y/control-has-associated-label']
            </issues>
        </input>

        <response>
            <grouping>
            **Group 1: Missing form label (line 4)**
            - Single issue: Input without label
            - Fix strategy: Add aria-label attribute
            </grouping>

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
                            <img src="banner.jpg" />
                            <input type="text" />
                            <input type="email" />
                        </div>
                    );
                };

                export default TestComponent;
            </file>

            <issues>
            ['4:7  error  img elements must have an alt prop, either with meaningful text, or an empty string for decorative images  jsx-a11y/alt-text',
             '5:7  error  img elements must have an alt prop, either with meaningful text, or an empty string for decorative images  jsx-a11y/alt-text',
             '6:7  error  A control must be associated with a text label  jsx-a11y/control-has-associated-label',
             '7:7  error  A control must be associated with a text label  jsx-a11y/control-has-associated-label']
            </issues>
        </input>

        <response>
            <grouping>
            **Group 1: Missing alt attributes (lines 4, 5)**
            - Both images lack alt attributes
            - Fix strategy: Add meaningful alt text to both images
            
            **Group 2: Missing form labels (lines 6, 7)**
            - Both inputs lack accessible labels
            - Fix strategy: Add aria-label to both form controls
            </grouping>

            <explanation>
            The two img elements lack alt attributes. I've added alt attributes with meaningful descriptions.
            The two input elements lack accessible labels. I've added aria-label attributes to provide text alternatives
            that screen readers can announce.
            </explanation>

            <file>
                const TestComponent = () => {
                    return (
                        <div>
                            <img src="logo.png" alt="Company logo" />
                            <img src="banner.jpg" alt="Welcome banner" />
                            <input type="text" aria-label="Name" />
                            <input type="email" aria-label="Email address" />
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

            <issues>
            ['5:7  error  Visible, non-interactive elements with click handlers must have at least one keyboard listener.  jsx-a11y/click-events-have-key-events',
             '5:7  error  Avoid non-native interactive elements. If using native HTML is not possible, add an appropriate role and support for tabbing, mouse, keyboard, and touch inputs to an interactive content element.  jsx-a11y/no-static-element-interactions']
            </issues>
        </input>

        <response>
            <grouping>
            **Group 1: Interactive div issues (line 5)**
            - Two related issues on same element: missing keyboard support and non-semantic element
            - Fix strategy: Replace div with semantic button element
            </grouping>

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
    Put your entire response in <response></response> tags. Structure your response as follows:

    1. First, wrap your grouping analysis in <grouping></grouping> tags. For each group, list:
       - Which issues belong together (by line number)
       - Why you're grouping them
       - What the common fix strategy will be

    2. Then wrap your detailed explanation in <explanation></explanation> tags.

    3. Finally, wrap your newly suggested file in <file></file> tags.
    """

    prompt = f"{TASK_CONTEXT}\n{TASK_DESCRIPTION}\n{EXAMPLES}\n{OUTPUT_FORMATTING}\n\n<input>\n<file>{formatted_file}</file>\n<issues>{a11y_issues}</issues>\n</input>"

    messages = [
        {"role": "user", "content": prompt},
    ]

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        temperature=0.2,
        messages=messages,
    )

    response_text = response.content[0].text

    # extract and print grouping analysis
    grouping_match = re.search(r'<grouping>(.*?)</grouping>', response_text, re.DOTALL)
    if grouping_match:
        print(grouping_match.group(1).strip())

    return response_text


# takes in a filepath and returns a list of a11y issues from linter
def get_a11y_issues(filepath: str):
    """
    Takes in a TSX/JSX file path and returns a list of accessibility issues
    detected by ESLint, plus the formatted file.

    Returns:
        issues (list[str]): List of formatted issue strings
        formatted_file (str): Prettier-formatted file contents
    """
    try:
        # format the file with Prettier first
        with open(filepath, "r") as f:
            rawfile = f.read().strip()

        prettier_process = subprocess.run(
            ["npx", "prettier", "--stdin-filepath", filepath],
            input=rawfile.encode("utf-8"),
            capture_output=True,
            check=True,
        )
        formatted_file = prettier_process.stdout.decode("utf-8")

        # run ESLint directly on file
        eslint_process = subprocess.run(
            ["npx", "eslint", filepath, "-f", "json"],
            capture_output=True,
            text=True,
            check=False,
        )

        # parse ESLint JSON output
        issues = []
        if eslint_process.stdout:
            eslint_results = json.loads(eslint_process.stdout)

            # extract issues from the first file
            if eslint_results and len(eslint_results) > 0:
                file_result = eslint_results[0]
                messages = file_result.get("messages", [])

                # filter for a11y issues and format them
                for msg in messages:
                    if msg.get("ruleId", "").startswith("jsx-a11y/"):
                        # format like ESLint's normal output
                        issue_str = f"{msg['line']}:{msg['column']}  error  {msg['message']}  {msg['ruleId']}"
                        issues.append(issue_str)

        return issues, formatted_file

    except Exception as e:
        print(f"Error: {e}")
        return [], ""

def parse_lighthouse_results(lighthouse_json):
    """
    Extract failed audits from Lighthouse JSON.
    """
    failed_audits = []
    audits = lighthouse_json.get("audits", {})
    
    for audit_id, audit_data in audits.items():
        if audit_data.get("score") == 0:
            details = audit_data.get("details", {})
            items = details.get("items", [])
            
            for item in items:
                node = item.get("node", {})
                failed_audits.append({
                    "audit_id": audit_id,
                    "title": audit_data.get("title", ""),
                    "selector": node.get("selector", ""),
                    "snippet": node.get("snippet", ""),
                    "explanation": node.get("explanation", "")
                })
    
    return failed_audits

def map_lighthouse_to_source(lighthouse_issues, tsx_source_code):
    """
    Use Claude to map Lighthouse issues to TSX source lines.
    """
    
    MAPPING_PROMPT = f"""
    You are mapping Lighthouse accessibility issues to specific lines in React/TSX source code.

    <tsx_source>
        {tsx_source_code}
    </tsx_source>

    <lighthouse_issues>
        {json.dumps(lighthouse_issues, indent=2)}
    </lighthouse_issues>

    Your task:
    1. For EACH Lighthouse issue, find the EXACT matching element in the TSX source
    2. Use ALL available information to match correctly:
        - Element type (button, p, div, img, etc.)
        - CSS selector path
        - Snippet content (especially style attributes and colors)
        - Explanation field (contains specific color values, sizes, etc.)
    3. Count line numbers carefully from line 1
    4. If you cannot confidently match an issue, SKIP it (do not guess)

    CRITICAL MATCHING RULES:
    - If explanation mentions "background: #007bff", find the element with that EXACT background color
    - If explanation mentions "color: #aaa", find the element with that EXACT text color
    - Match element TYPE first (button vs p vs div), then match by styles
    - A color-contrast issue on a <button> should NOT map to a <p> tag
    - When in doubt about which element, look at the "snippet" field for exact HTML

    Output ONLY valid JSON array (no other text):
    [
    {{
        "line": <line_number>,
        "column": 7,
        "message": "<concise description>",
        "rule": "lighthouse/<audit_id>"
    }}
    ]

    Example of CORRECT mapping:
    - Lighthouse: "color-contrast issue, snippet: <button style='background: #007bff'>"
    - TSX has button on line 62 with background: "#007bff"
    - Correct output: {{"line": 62, "message": "...", "rule": "lighthouse/color-contrast"}}

    Example of INCORRECT mapping:
    - Lighthouse: "color-contrast issue, snippet: <button style='background: #007bff'>"  
    - TSX has <p> on line 80 with color: "#4a4a4a"
    - WRONG to map to line 80 - different element type and different style!
    """
    
    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        temperature=0,
        messages=[{"role": "user", "content": MAPPING_PROMPT}]
    )
    
    response_text = response.content[0].text
    
    # extract JSON from response
    json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if json_match:
        try:
            mapped_issues = json.loads(json_match.group(0))
            
            # log for debugging
            print(f"\n[debug] LLM mapped {len(mapped_issues)} issues")
            for issue in mapped_issues:
                print(f"  line {issue.get('line')}: {issue.get('rule')}")
            
            return mapped_issues
        except json.JSONDecodeError as e:
            print(f"error: could not parse LLM response as JSON: {e}")
            return []
    
    print("error: no JSON array found in LLM response")
    return []

def normalize_lighthouse_issues(mapped_issues):
    """
    Convert to linter-style format.
    """
    normalized = []
    for issue in mapped_issues:
        line = issue.get("line", 0)
        column = issue.get("column", 7)
        message = issue.get("message", "")
        rule = issue.get("rule", "lighthouse/unknown")
        issue_str = f"{line}:{column}  error  {message}  {rule}"
        normalized.append(issue_str)
    return normalized


def get_lighthouse_issues(tsx_file_path):
    """
    High-level function that orchestrates everything.
    Similar to get_a11y_issues() but for runtime analysis.
    """
    # import server function
    import sys
    sys.path.append('../server')
    
    # run lighthouse (returns raw JSON)
    lighthouse_json = run_lighthouse_analysis()
    
    # parse failures
    failed_audits = parse_lighthouse_results(lighthouse_json)
    
    # read TSX source
    with open(tsx_file_path, 'r') as f:
        tsx_source = f.read()
    
    # map to lines
    mapped_issues = map_lighthouse_to_source(failed_audits, tsx_source)
    
    # normalize to linter format
    normalized_issues = normalize_lighthouse_issues(mapped_issues)
    
    return normalized_issues