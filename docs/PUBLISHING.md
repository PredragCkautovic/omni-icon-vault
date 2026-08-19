# Publishing Omni Icon Vault on GitHub

The repository tree is already prepared for GitHub.

## 1. Create the repository locally

From the extracted project folder:

```bash
git init
git add .
git commit -m "Omni Icon Vault 4.0.0"
git branch -M main
```

## 2. Create an empty GitHub repository

Create a new repository in the GitHub UI. Do **not** add a generated README/LICENSE there because this project already includes them.

Then connect and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/omni-icon-vault.git
git push -u origin main
```

If you use GitHub CLI:

```bash
gh repo create omni-icon-vault --public --source=. --remote=origin --push
```

## 3. Recommended repository settings

- Enable Issues and Discussions if you want community support.
- Enable **Security → Private vulnerability reporting**.
- Protect `main` and require the `CI` workflow before merge.
- Keep GitHub Actions enabled; the included workflow tests Windows, macOS and Linux.

## 4. Publish the first release

```bash
git tag v4.0.0
git push origin v4.0.0
```

The included `release.yml` workflow runs the test matrix, builds platform release ZIPs and creates a GitHub Release automatically.

## What must never be committed

The `.gitignore` intentionally excludes:

- `vendor/` downloaded icon source trees
- `cache/` upstream archives
- generated icon index files
- locally collected favicon files/registry
- installed-state data

This keeps the public repository small and avoids accidentally redistributing user favicon data.
