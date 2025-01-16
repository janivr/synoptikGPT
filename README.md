# Synoptik Real Estate Portfolio Assistant (synoptikGPT)

## Overview
Synoptik is an AI-powered real estate portfolio management tool that provides insights, analytics, and intelligent querying capabilities.

## Features
- Building Portfolio Management
- Financial Analysis
- Natural Language Querying
- Modular Architecture

## Setup
1. Clone the repository.
2. Create a virtual environment.
3. Install dependencies: `pip install -e .[dev]`.
4. Set up a `.env` file with your OpenAI API key.
5. Run the app: `streamlit run src/app.py`.

## Testing
- Run tests: `pytest`.
- Generate a coverage report: `pytest --cov=src`.

## Development
- Code formatter: Black.
- Linter: Flake8.
- Type checking: MyPy.
