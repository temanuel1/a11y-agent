# a11y Agent

An automated accessibility fixing agent that detects and resolves both static and runtime accessibility issues in React/TypeScript components.

## Overview

This agent uses a two-phase approach to ensure comprehensive accessibility compliance:

**Phase 1: Static Analysis** - ESLint with jsx-a11y rules detects code-level issues (missing alt text, unlabeled inputs, etc.)

**Phase 2: Runtime Analysis** - Lighthouse detects visual issues (color contrast, touch target sizes) by rendering components in a browser

Claude is used to intelligently group related issues, generate WCAG-compliant fixes, and map runtime issues back to source code lines.

## Setup

1. Install Node.js dependencies:

```bash
npm install eslint eslint-plugin-jsx-a11y prettier vite lighthouse
```

2. Install Python dependencies:

```bash
pip install anthropic python-dotenv
```

3. Create a `.env` file with your Anthropic API key:

```
ANTHROPIC_API_KEY=your_key_here
```

4. Set up the server template:

```bash
cd server/template
npm install
```

## Usage

Run the agent on a file:

```bash
cd agent
python3 agent.py
```

Edit the file path at the bottom of `agent.py` to target different files.

## How It Works

### Phase 1: Static Analysis

1. Runs ESLint with jsx-a11y rules to detect code-level issues
2. Uses Claude to group related issues and generate fixes
3. Applies fixes iteratively until all static issues are resolved
4. Creates a backup in `.backups/` directory

### Phase 2: Runtime Analysis

1. Copies the fixed file to `server/template/`
2. Starts a Vite dev server to render the component
3. Runs Lighthouse accessibility audits
4. Uses Claude to map DOM-level issues to source code line numbers
5. Fixes runtime issues (color contrast, touch targets, etc.)
6. Repeats until all issues are resolved or deadlock is detected

### Deadlock Detection

The agent detects when the same issue types repeat for 3+ rounds and stops to prevent infinite loops, indicating issues that may require manual review.

## Features

- **Comprehensive Coverage**: Catches both code-level and visual accessibility issues
- **Intelligent Grouping**: Groups related issues to avoid fix conflicts
- **Accurate Mapping**: Maps runtime DOM issues to specific source code lines
- **Automatic Backup**: Saves original files to `.backups/` directory
- **Clean Output**: Lighthouse reports saved to `.lighthouse-reports/` directory
- **Iterative Fixing**: Applies fixes and re-validates until component is fully accessible

## Common Issues Fixed

**Static Analysis:**

- Missing alt text on images
- Unlabeled form controls
- Non-semantic interactive elements (divs with onClick)
- Missing button types
- Keyboard navigation issues

**Runtime Analysis:**

- Insufficient color contrast ratios
- Touch targets too small
- Missing semantic landmarks
- Visual-only information

## Project Structure

```
a11y-agent/
├── agent/
│   ├── agent.py          # Main orchestration logic
│   ├── tools.py          # ESLint, Lighthouse, and LLM integration
│   └── test.tsx          # Component to analyze
├── server/
│   ├── server.py         # Vite server and Lighthouse runner
│   └── template/         # Test harness for rendering components
├── .backups/             # Backup files (gitignored)
├── .lighthouse-reports/  # Lighthouse JSON reports (gitignored)
└── .env                  # API keys (gitignored)
```

## Configuration

The ESLint configuration in `.eslintrc.json` defines which accessibility rules to check. The agent's prompts and fix patterns are defined in `tools.py`.

## Limitations

- Cannot detect all accessibility issues (e.g., keyboard focus traps require manual testing)
- Color contrast fixes may require multiple iterations to find optimal values
- Works best with standard React components; complex dynamic components may need manual review
