import os

def print_tree(root, indent=""):
    try:
        entries = sorted(os.listdir(root))
    except Exception as e:
        print(indent + f"[ERROR opening {root}: {e}]")
        return

    for name in entries:
        path = os.path.join(root, name)
        if os.path.isdir(path):
            print(indent + "📁", name)
            print_tree(path, indent + "   ")
        else:
            print(indent + "📄", name)

# Use this to list everything under your local safeguard folder
project_root = r"ppe_detection"  # change this
print_tree(project_root)