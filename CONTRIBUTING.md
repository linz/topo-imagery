# Contributing

## Coding guidelines

### Core principles

#### Readibility

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

   Keep consistent naming accross modules for things that have the same purpose. For example, a CLI argument for the source files to take in input, should not be `source` somewhere and `input` or `path` somewhere else.

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
