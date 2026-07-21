# Contributing to GreenHawk AI

Thank you for your interest in contributing to GreenHawk AI.

This document explains the recommended workflow for contributing code,
documentation, improvements, and bug fixes.

---

# How to Contribute

## 1. Fork the Repository

Create your own fork of the project repository.

## 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/GreenHawk-AI.git

cd GreenHawk-AI
```

---

# Development Workflow

Create a new branch before making changes:

```bash
git checkout -b feature/new-feature
```

Recommended branch naming:

```
feature/
bugfix/
documentation/
refactor/
```

Examples:

```
feature/add-new-model

bugfix/fix-upload-error

documentation/update-readme
```

---

# Code Style

## Python Backend

Follow:

- PEP 8
- Clear naming conventions
- Modular design
- Type hints where possible

## Frontend

Keep:

- Clean JavaScript structure
- Reusable components
- Consistent formatting

---

# Adding New AI Models

When adding a new AI model:

Please include:

- Model description
- Official source
- License information
- Required dependencies
- Example usage

The model should be integrated through the existing service architecture.

---

# Testing Changes

Before submitting changes:

Check:

- Backend starts correctly
- API endpoints work
- Frontend loads correctly
- Image processing pipeline works

---

# Commit Messages

Use meaningful commit messages.

Good:

```
Add DeOldify processing service
Fix RTL comparison slider issue
Improve image validation
```

Avoid:

```
update
fix
changes
```

---

# Pull Requests

A Pull Request should include:

- Description of changes
- Reason for changes
- Testing information
- Screenshots if UI changes are included

---

# Questions

For questions or discussions, open an Issue.

Thank you for helping improve GreenHawk AI.
```