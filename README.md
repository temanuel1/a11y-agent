# a11y Agent

An automated accessibility fixing agent that detects and resolves accessibility issues in React/TypeScript components.

## Overview

This agent uses ESLint with jsx-a11y rules to detect accessibility issues, then uses Claude to intelligently group related issues and generate fixes that comply with WCAG standards.

## Setup

1. Install dependencies:

```bash
npm install eslint eslint-plugin-jsx-a11y prettier
```

2. Install Python dependencies:

```bash
pip install anthropic python-dotenv
```

3. Create a `.env` file with your Anthropic API key:

```
ANTHROPIC_API_KEY=your_key_here
```

## Usage

Run the agent on a file:

```bash
python3 agent.py
```

Edit the file path in `agent.py` to target different files.

## How It Works

1. Runs ESLint to detect accessibility issues
2. Uses Claude to intelligently group related issues
3. Generates fixes for each group using Claude
4. Applies fixes sequentially, updating the file after each group
5. Creates a backup with `_old.tsx` extension

## Features

- Intelligent issue grouping to avoid fix conflicts
- Fixes common issues like missing alt text, unlabeled form controls, and non-semantic interactive elements
- Preserves code formatting with Prettier
- Automatic backup of original files

## Configuration

The ESLint configuration in `.eslintrc.json` defines which accessibility rules to check. The agent's fix patterns are defined in `tools.py`.
