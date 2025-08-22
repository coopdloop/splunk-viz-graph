# Contributing to Splunk Vendor Query

Thank you for your interest in contributing to this project! This guide will help you get started.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Access to a Splunk environment for testing

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/splunk-vendor-query.git
   cd splunk-vendor-query
   ```

2. **Install dependencies**
   ```bash
   uv sync --dev
   ```

3. **Set up configuration**
   ```bash
   cp config/environments.json.example config/environments.json
   # Edit config/environments.json with your Splunk environment details
   ```

4. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

5. **Run tests to verify setup**
   ```bash
   uv run pytest
   ```

## Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write tests for new functionality
   - Update documentation as needed
   - Follow the existing code style

3. **Run quality checks**
   ```bash
   # Run tests
   uv run pytest
   
   # Run linting
   uv run ruff check .
   
   # Run formatting
   uv run black .
   
   # Run security checks
   uv run bandit -r src/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### Commit Message Format

We follow conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

### Pull Request Process

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request**
   - Use a clear, descriptive title
   - Fill out the PR template
   - Link any related issues
   - Ensure all CI checks pass

3. **Code Review**
   - Address feedback promptly
   - Keep discussions constructive
   - Update your branch as needed

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_splunk_client.py
```

### Test Guidelines

- Write tests for all new functionality
- Maintain or improve test coverage
- Use descriptive test names
- Mock external dependencies (Splunk API calls)

## Code Style

We use automated tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting and import sorting
- **Bandit** for security scanning
- **MyPy** for type checking

These tools run automatically via pre-commit hooks and CI.

## Documentation

- Update docstrings for new functions/classes
- Update README.md for user-facing changes
- Add examples for new features
- Keep documentation clear and concise

## Security

- Never commit real credentials or tokens
- Use the template configuration files
- Run security scans before submitting
- Report security issues privately (see [SECURITY.md](SECURITY.md))

## Issue Guidelines

### Bug Reports

- Use the bug report template
- Include steps to reproduce
- Provide system information
- Include relevant log outputs

### Feature Requests

- Use the feature request template
- Explain the use case
- Describe the proposed solution
- Consider alternatives

## Getting Help

- Check existing issues and discussions
- Review the documentation
- Ask questions in issues (use the question label)
- Join discussions in pull requests

## Recognition

Contributors are recognized in several ways:
- Listed in the project's contributors
- Mentioned in release notes for significant contributions
- Added to the project's README

## License

By contributing, you agree that your contributions will be licensed under the MIT License.