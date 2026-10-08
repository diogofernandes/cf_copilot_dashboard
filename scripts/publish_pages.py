"""Publish the static site to the personal repository; never the team repository."""
import shutil
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TARGET = "https://github.com/diogofernandes/cf_copilot_dashboard.git"
WORK = ROOT / ".runtime/pages-publication"
def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()
WORK.parent.mkdir(parents=True, exist_ok=True)
if not (WORK / ".git").exists():
    git("clone", "--branch", "gh-pages", "--single-branch", TARGET, str(WORK))
if git("remote", "get-url", "origin", cwd=WORK) != TARGET:
    raise RuntimeError("Publication remote is not Diogo's personal repository.")
git("pull", "--ff-only", cwd=WORK)
for source in (ROOT / "docs/site").iterdir():
    if source.is_file():
        shutil.copy2(source, WORK / source.name)
for key in ("user.name", "user.email"):
    git("config", key, git("config", key), cwd=WORK)
git("add", ".", cwd=WORK)
if git("diff", "--cached", "--name-only", cwd=WORK):
    git("commit", "-m", "Update interactive portfolio showcase", cwd=WORK)
    git("-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
        "push", "origin", "gh-pages", cwd=WORK)
print("Published:", TARGET)
