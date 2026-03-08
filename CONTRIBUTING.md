# Contributing

## Table of Contents

- [Coding guidelines](#coding-guidelines)
  - [Core principles](#core-principles)
    - [Readability](#readability)
    - [Consistency](#consistency)
    - [Focused changes](#focused-changes)
    - [Documentation](#documentation)
  - [Testing](#testing)
    - [Coverage](#coverage)
      - [New Features](#new-features)
      - [Bug Fixes](#bug-fixes)
    - [Structure](#structure)
      - [Clarity](#clarity)
      - [Isolation](#isolation)
      - [Focused](#focused)
    - [Names](#names)
    - [Organisation](#organisation)

## Coding guidelines

### Core principles

#### Readability

Write code others can understand quickly.

- avoid "clever" shortcuts

  ```python
  # can be confusing
  inside = [pt for pt in points if polygons.contains(pt)]

  # more readable
  inside_points = []
  for point in points:
   if polygon.contains(point):
       inside_points.append(point)
  ```

  - Each step is explicit: iterating, testing, appending
  - Easier to debug as you can add a trigger point per step

- avoid deeply nested logic: use early returns when possible

#### Consistency

The code should follow the same **patterns, naming conventions, formatting and structure** across the repository. When the code looks familiar, it's easier to read, review and maintain.

- **Naming**

  Keep consistent naming across modules for things that have the same purpose. For example, a CLI argument for the source files to take in input, should not be `source` somewhere and `input` or `path` somewhere else.

- **Structure**
  - Maintain the same folder and module pattern accross the repository
  - Keep similar types of functions grouped together

#### Focused changes

Each PR should do **one thing**. Avoid mixing unrelated features, refactors or bug fixes in the same change.

Focused changes make it easier to:

- understand what the change is about
- review the code
- revert or debug the code if something breaks
- track history in Git

It is OK to have small refactoring or fixing typos in a change when it is related to the change. **If the refactoring is too big and impact other features, they should be treated as separate changes**.

#### Documentation

Comments in the code should explain _why_ a piece of code exists or _why_ an approach was chosen, not _what_ the code does.

The goal is to communicate the **reasoning, decisions, and assumptions** where it is not obvious so the reader can clearly understand.

It makes the code easier to refactor or extend without breaking something. It also helps reviewers to understand the context quickly without having to ask questions or make researches.

Where possible, prefer executable documentation such as `doctest` over explanatory comments.  
`doctest` documents expected behavior through concrete examples that are automatically verified by running the tests pipeline.

This keeps documentation and behavior in sync, reduces the risk of outdated comments, and provides both usage examples and regression protection at the same time.

### Testing

Tests are required for all non-trivial behavior.

Testing is not optional or “added later.”
It is part of the implementation.

A good test suite should:

- Increase confidence
- Encourage refactoring
- Prevent regressions
- Reduce fear of change
- Help contributors understand the codebase

Tests serve as documentation:

- How function are expected to be used
- What inputs are valid
- What outputs are expected
- What errors should be raised

#### Coverage

When to write tests?

- When adding a new functionality
- Before refactoring if not existing for what is going to be refactored
- Before fixing complex bugs
- When behaviour is ambiguous
- When adding new branches / edge cases

Focus on:

- Testing important logic
- Covering edge cases
- Verifying actual outcomes

##### New Features

All new features must include tests that verify:

- Expected behavior
- Edge cases
- Failure scenarios (when applicable)

A feature is not complete without tests.

##### Bug Fixes

Every bug fix must include a regression test that:

- Reproduces the original bug
- Verify the correct behavior
- Prevent the same bug from reappearing

This ensures the same issue cannot silently reappear in the future.

#### Structure

##### Clarity

Tests should be as readable as production code.

A good test:

- Is easy to understand without reading the implementation
- Clearly communicates what is being validated
- Has minimal setup noise

##### Isolation

Tests must not depend on:

- Execution order
- Shared mutable state
- Data left behind by other tests
- Each test should be runnable independently.

##### Focused

Each test should verify one logical behavior.

If a test fails, it should be immediately clear why.

#### Names

Test names should describe the expected behaviour.
Pattern: `test_<expected_behaviour>_when_<condition>`

The reader should understand the behaviour without reading the test definition.

Examples:

```python
test_returns_empty_list_when_input_is_empty
test_raises_value_error_for_invalid_path
```

#### Organisation

- Group related tests together
- Keep test files aligned with module structure

Example:

```text
stac/imagery/
          collection.py

stac/imagery/tests/
              collection_test.py
```
