import subprocess
import os
import sys
from pathlib import Path

def update_gh_pages():
    workspace = Path(__file__).resolve().parent.parent
    html_file = workspace / "website" / "index.html"
    if not html_file.exists():
        html_file = workspace / "scratch" / "gh_pages_index_built.html"
    
    if not html_file.exists():
        print(f"Error: {html_file} does not exist. Ejecute primero scripts/rebuild_gh_pages.py")
        sys.exit(1)

    # 1. Hash object to create blob
    res = subprocess.run(["git", "hash-object", "-w", str(html_file)], cwd=str(workspace), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error creating blob: {res.stderr}")
        sys.exit(1)
    blob_id = res.stdout.strip()
    print(f"Created blob: {blob_id}")

    # 2. Get tree of origin/gh-pages or local gh-pages
    res = subprocess.run(["git", "ls-tree", "origin/gh-pages"], cwd=str(workspace), capture_output=True, text=True)
    if res.returncode != 0:
        res = subprocess.run(["git", "ls-tree", "gh-pages"], cwd=str(workspace), capture_output=True, text=True)

    if res.returncode != 0:
        print(f"Error reading gh-pages tree: {res.stderr}")
        sys.exit(1)
    
    entries_dict = {}
    for line in res.stdout.strip().splitlines():
        line = line.strip().replace("\r", "")
        parts = line.split(maxsplit=3)
        if len(parts) == 4:
            mode, typ, sha, name = parts
            name = name.strip('"').strip("'")
            entries_dict[name] = (mode, typ, sha)
    
    # Update index.html
    entries_dict["index.html"] = ("100644", "blob", blob_id)
    
    new_tree_entries = []
    for name in sorted(entries_dict.keys()):
        mode, typ, sha = entries_dict[name]
        new_tree_entries.append(f"{mode} {typ} {sha}\t{name}")

    # 3. Write tree using git mktree in binary mode (avoids Windows \r\n newline translation)
    mktree_bytes = ("\n".join(new_tree_entries) + "\n").encode("ascii")
    res = subprocess.run(["git", "mktree"], input=mktree_bytes, cwd=str(workspace), capture_output=True)
    if res.returncode != 0:
        print(f"Error creating tree: {res.stderr.decode('utf-8', errors='ignore')}")
        sys.exit(1)
    tree_id = res.stdout.decode('ascii').strip()
    print(f"Created clean tree: {tree_id}")

    # 4. Get current commit of origin/gh-pages or local gh-pages
    res = subprocess.run(["git", "rev-parse", "origin/gh-pages"], cwd=str(workspace), capture_output=True, text=True)
    if res.returncode != 0:
        res = subprocess.run(["git", "rev-parse", "gh-pages"], cwd=str(workspace), capture_output=True, text=True)
    parent_commit = res.stdout.strip() if res.returncode == 0 else None

    # 5. Commit tree
    commit_cmd = ["git", "commit-tree", tree_id, "-m", "chore(web): update gh-pages showcase with live simulators and release sync"]
    if parent_commit:
        commit_cmd.extend(["-p", parent_commit])
    
    res = subprocess.run(commit_cmd, cwd=str(workspace), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error creating commit: {res.stderr}")
        sys.exit(1)
    new_commit_id = res.stdout.strip()
    print(f"Created commit: {new_commit_id}")

    # 6. Update ref gh-pages
    res = subprocess.run(["git", "update-ref", "refs/heads/gh-pages", new_commit_id], cwd=str(workspace), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error updating ref: {res.stderr}")
        sys.exit(1)
    
    print(f"SUCCESS: gh-pages branch updated to {new_commit_id} without checkout collisions!")

if __name__ == "__main__":
    update_gh_pages()
