# Project Structure Refactor Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Reorganize the `Sak-Family-Agent` repository into a more logical and scalable structure. This involves standardizing service and persona layouts, cleaning up obsolete files, and improving the top-level organization.

**Architecture:** The proposed structure will clearly separate `services`, `personas`, and shared `skills`. Each service and persona will be a self-contained module. A top-level `docs` directory will centralize project documentation.

**Tech Stack:** File system operations (move, delete, create directory).

---

### Task 1: Move the root `pitch.md` into the `hf-training-jobs` service

**Objective:** Relocate the misplaced `pitch.md` file to its correct service directory, `services/hf-training-jobs`. This file was created in a previous step but placed in the wrong location.

**Files:**

- Delete: `pitch.md`
- Create: `services/hf-training-jobs/pitch.md`

**Step 1: Move the file**

```bash
mv pitch.md services/hf-training-jobs/pitch.md
```

**Step 2: Commit**

```bash
git add docs/
git commit -m "feat: create top-level docs directory"
```

---

### Task 2: Move the root `pitch.md` into the `hf-training-jobs` service

**Objective:** Relocate the misplaced `pitch.md` file to its correct service directory, `services/hf-training-jobs`.

**Files:**

- Delete: `pitch.md`
- Create: `services/hf-training-jobs/pitch.md`

**Step 1: Move the file**

```bash
mv pitch.md services/hf-training-jobs/pitch.md
```

**Step 2: Commit**

```bash
git add pitch.md services/hf-training-jobs/pitch.md
git commit -m "refactor: move hf-training-jobs pitch to service dir"
```

---

### Task 3: Clean up the obsolete `training` directory

**Objective:** Remove the old `training` directory, which was superseded by the `services/hf-training-jobs` service.

**Files:**

- Delete: `training/`

**Step 1: Remove the directory**

```bash
rm -rf training/
```

**Step 2: Commit**

```bash
git add training/
git commit -m "refactor: remove obsolete training directory"
```

---

### Task 4: Standardize the `personas` skill structure

**Objective:** Consolidate all skills into a single top-level `skills` directory to promote sharing and simplify persona definitions. Personas will no longer contain their own `skills` subdirectories.

**Files:**

- Create: `skills/`
- Modify: `personas/sakking/skills/` -> `skills/business/`
- Modify: `personas/sakthai/skills/` -> `skills/mlops/`
- Modify: `personas/shared/skills/` -> `skills/`

**Step 1: Create the top-level `skills` directory**

```bash
mkdir skills
```

**Step 2: Move all existing skills into the new directory**

```bash
mv personas/shared/skills/* skills/
mv personas/sakking/skills/business skills/
mv personas/sakthai/skills/mlops/hf-accelerate.md skills/mlops/
rm -rf personas/sakking/skills personas/sakthai/skills personas/shared/
```

**Step 3: Commit**

```bash
git add .
git commit -m "refactor: consolidate all skills into a single top-level directory"
```
