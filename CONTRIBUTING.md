# Contributing to Lead Generator Pro

Thanks for your interest in contributing! Here's how to get started.

## How to Contribute

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-new-feature`
3. **Commit** your changes: `git commit -m "Add my new feature"`
4. **Push** to the branch: `git push origin feature/my-new-feature`
5. **Open** a Pull Request

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/lead-generator-pro.git
cd lead-generator-pro
pip install -r requirements.txt
python main.py
```

## Guidelines

- **Code style**: Follow existing patterns in the codebase
- **No API keys**: Keep the project free — no paid service integrations
- **Thread safety**: All new scrapers must be thread-safe
- **Error handling**: Use try/except with graceful fallbacks
- **Testing**: Test your changes before submitting

## Reporting Issues

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Full error traceback

## Feature Requests

Open an issue with:
- Clear description of the feature
- Use case (why it's needed)
- Example output if applicable

## License

By contributing, you agree that your contributions will be licensed under the same CC BY-NC 4.0 license.
