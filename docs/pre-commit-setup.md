# Pre-Commit Hook Setup

## What We Installed

Pre-commit hooks that run automatically before every `git commit` to prevent accidentally committing sensitive data.

## What It Checks For

1. **AWS ARNs with account IDs** - Pattern: `arn:aws:service:region:123456789012:...`
2. **AWS Access Keys** - Pattern: `AKIA[0-9A-Z]{16}`
3. **Hardcoded AWS credentials** - Patterns: `aws_secret_access_key=`, `aws_access_key_id=`
4. **Private SSH keys** - Detects `.pem`, `.key` files and private key content
5. **Other secrets** - Uses detect-secrets tool to find potential secrets
6. **Code formatting** - Runs Black formatter automatically

## How It Works

```bash
# You make changes and stage them
git add myfile.py

# You try to commit
git commit -m "my changes"

# ⚡ Pre-commit hooks run automatically BEFORE the commit
#    - Scans staged files for secrets/ARNs
#    - Checks for private keys
#    - Runs code formatter

# If issues found:
❌ COMMIT BLOCKED
Shows you exactly what was found and where

# If all clean:
✅ COMMIT PROCEEDS
```

## Where It Scans

- ✅ **Code files**: `*.py`, `*.json`, `*.yaml`, `*.yml`
- ❌ **Excluded**: `docs/`, `specs/` (documentation can have example ARNs)

This means you can safely have example ARNs in documentation, but real ARNs in code will be caught!

## Testing It

To manually run all hooks on all files:
```bash
source .venv/bin/activate
pre-commit run --all-files
```

To run just the ARN checker:
```bash
source .venv/bin/activate
pre-commit run check-aws-credentials --all-files
```

## Example: What Gets Blocked

If you try to commit a Python file with:
```python
# ❌ This will be blocked
role_arn = "arn:aws:iam::568790270051:role/MySecretRole"
access_key = "AKIAIOSFODNN7EXAMPLE"  # pragma: allowlist secret
```

You'll see:
```
❌ Found potential AWS credentials or real ARNs in code!
./cdk/config.py:15: arn:aws:iam::568790270051:role/MySecretRole
```

## Best Practices

✅ **DO**:
- Use environment variables: `os.getenv("ROLE_ARN")`
- Use AWS SSM Parameter Store
- Use CDK outputs/references between stacks
- Document example ARNs in `docs/` folder

❌ **DON'T**:
- Hardcode ARNs with real account numbers in code
- Commit AWS access keys
- Disable the hooks without team approval

## Installed For

- ✅ Your local machine (already done)
- ✅ Every team member (when they run `pre-commit install` after pulling this config)
- ✅ **CI/CD** (GitHub Actions) - Enforced for all PRs!

## Team Setup

### For Each Team Member

After pulling this code, run once:
```bash
cd infra
pip install pre-commit
pre-commit install
```

That's it! Now hooks run automatically on their machine.

### CI/CD Enforcement (Already Done! ✅)

GitHub Actions now runs pre-commit checks on EVERY PR:
- **Job**: `pre-commit` (runs before lint, tests, etc.)
- **What it does**: Scans all files for secrets/credentials
- **Result**: PR will fail if secrets are detected

**This means even if someone bypasses local hooks (with `--no-verify`), CI will catch it!** 🛡️

## Files Added

1. `.pre-commit-config.yaml` - Hook configuration (committed to repo)
2. `.gitignore` - Added `*.arn` to ignore ARN files
3. `cdk/requirements.txt` - Added `pre-commit>=3.5.0`
