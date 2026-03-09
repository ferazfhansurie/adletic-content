# Skill: Course Outline Builder

Structure a new course or workshop for the AI Video Creators Community.

## Input
Ask the user for:
- **Course topic** — What will students learn?
- **Skill level** — Beginner, intermediate, advanced
- **Target outcome** — What can they DO after completing it?
- **Estimated lessons** — Rough number or let me suggest
- **Price point** — To calibrate depth and value

## Process
1. Define the transformation (before → after)
2. Break into modules (3-5 modules)
3. Break each module into lessons with clear titles
4. For each lesson: one-line description + deliverable/exercise
5. Suggest a bonus or resource pack to increase perceived value

## Output
Save to `outputs/courses/` with the course name as filename.

## Structure
```
Course: [Name]
Transformation: [Before state] → [After state]
Lessons: X | Price: RMX

Module 1: [Name]
  Lesson 1.1: [Title] — [What they learn/do]
  Lesson 1.2: ...

Bonus: [Resource/template/prompt pack]
```
