import os

def print_tree(root, indent=""):
    # Define files and folders to ignore
    ignored_items = {
        "venv", 
        ".venv", 
        "env", 
        ".git", 
        "__pycache__", 
        ".pytest_cache", 
        ".idea", 
        ".vscode",
        ".DS_Store"
    }
    
    try:
        entries = sorted(os.listdir(root))
    except Exception as e:
        print(indent + f"[ERROR opening {root}: {e}]")
        return

    for name in entries:
        # Skip ignored folder and file names
        if name in ignored_items:
            continue
            
        path = os.path.join(root, name)
        if os.path.isdir(path):
            print(indent + "📁", name)
            print_tree(path, indent + "    ")
        else:
            print(indent + "📄", name)

# Target directory path
project_root = r"ppe_detection" 
print_tree(project_root)
