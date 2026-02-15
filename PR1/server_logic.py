import os

def find_filename(filename):
    safe_filename = os.path.basename(filename)
    for root, dirs, files in os.walk('.'):
        if safe_filename in files:
            full_path = os.path.join(root,safe_filename)
            if os.path.isfile(full_path):
                print(f"File {safe_filename} was found at {full_path}")
                return full_path
            else :
                print(f"File {safe_filename} was found at {full_path} but it is not a regular file.")
                return None
        else:
            print(f"File {safe_filename} was not found in the current directory or its subdirectories")
            return None
        

    