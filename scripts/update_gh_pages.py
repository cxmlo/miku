import subprocess
import os

def update_gh_pages():
    workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_file = os.path.join(workspace, "scratch", "gh_pages_index_built.html")
    
    if not os.path.exists(html_file):
        print(f"Error: {html_file} does not exist")
        return

    # 1. Hash object to create blob
    res = subprocess.run(["git", "hash-object", "-w", html_file], cwd=workspace, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error creating blob: {res.stderr}")
        return
    blob_id = res.stdout.strip()
    print(f"Created blob: {blob_id}")

    # 2. Get tree of current gh-pages
    res = subprocess.run(["git", "ls-tree", "gh-pages"], cwd=workspace, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error reading gh-pages tree: {res.stderr}")
        return
    
    lines = res.stdout.strip().splitlines()
    new_tree_entries = []
    found = False
    for line in lines:
        parts = line.split(maxsplit=3)
        if len(parts) == 4:
            mode, typ, sha, name = parts
            if name == "index.html":
                new_tree_entries.append(f"{mode} {typ} {blob_id}\t{name}")
                found = True
            else:
                new_tree_entries.append(line)
    
    if not found:
        new_tree_entries.append(f"100644 blob {blob_id}\tindex.html")

    # 3. Write tree using git mktree
    mktree_input = "\n".join(new_tree_entries) + "\n"
    res = subprocess.run(["git", "mktree"], input=mktree_input, cwd=workspace, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error creating tree: {res.stderr}")
        return
    tree_id = res.stdout.strip()
    print(f"Created tree: {tree_id}")

    # 4. Get current commit of gh-pages
    res = subprocess.run(["git", "rev-parse", "gh-pages"], cwd=workspace, capture_output=True, text=True)
    parent_commit = res.stdout.strip() if res.returncode == 0 else None

    # 5. Commit tree
    commit_cmd = ["git", "commit-tree", tree_id, "-m", "chore(web): update gh-pages landing page with Ko-fi hero placement and Island updates"]
    if parent_commit:
        commit_cmd.extend(["-p", parent_commit])
    
    res = subprocess.run(commit_cmd, cwd=workspace, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error creating commit: {res.stderr}")
        return
    new_commit_id = res.stdout.strip()
    print(f"Created commit: {new_commit_id}")

    # 6. Update ref gh-pages
    res = subprocess.run(["git", "update-ref", "refs/heads/gh-pages", new_commit_id], cwd=workspace, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error updating ref: {res.stderr}")
        return
    
    print(f"SUCCESS: gh-pages branch updated to {new_commit_id} without checkout collisions!")

if __name__ == "__main__":
    update_gh_pages()
