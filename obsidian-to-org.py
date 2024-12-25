import sys
import re
import os
import uuid

def replace(pattern, substitution, filename):
    with open(filename, "r+") as f:
        content = f.read()
        content = re.sub(pattern, substitution, content)
        f.seek(0)
        f.write(content)
        f.truncate()

def generate_org_roam_header(file_path, tags):
    """Generate Org-roam file header with a unique ID, title, and tags."""
    title = os.path.splitext(os.path.basename(file_path))[0]
    unique_id = str(uuid.uuid4())
    tags_line = f"#+filetags: {tags}" if tags else "#+filetags:"
    header = f"#+title: {title}\n{tags_line}\n#+roam_aliases: \n#+id: {unique_id}\n\n"
    return header

def extract_and_convert_tags(content):
    """Extract Obsidian-style tags block and convert them to Org-roam tags."""
    # Match Obsidian tags block (e.g., "tags: - tag1 - tag2")
    tags_block_pattern = re.compile(r"tags:\s*(-\s+\w+\s*)+")
    tag_pattern = re.compile(r"-\s+(\S+)")

    tags = ""
    def transform_tags_block(match):
        nonlocal tags
        tags_block = match.group(0)
        tag_list = tag_pattern.findall(tags_block)
        tags = ":" + ":".join(tag_list) + ":"
        return ""  # Remove the matched block from the content

    content = re.sub(tags_block_pattern, transform_tags_block, content)
    return content, tags

def remove_md_header(content):
    """Remove Markdown header lines (starting and ending with ---)."""
    md_header_pattern = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
    return re.sub(md_header_pattern, "", content)

def convert_file(md_file, out_dir, relative_path):
    # Ensure the output directory retains the relative path structure
    target_dir = os.path.join(out_dir, relative_path)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    org_file = os.path.splitext(md_file)[0] + ".org"
    org_file = os.path.join(target_dir, os.path.basename(org_file))

    with open(md_file, "r") as f:
        content = f.read()

    # Extract and convert tags
    content, tags = extract_and_convert_tags(content)

    # Remove Markdown header
    content = remove_md_header(content)

    # Convert from md to org using Pandoc
    temp_md_file = os.path.join(target_dir, os.path.basename(md_file))  # Temp file for Pandoc
    with open(temp_md_file, "w") as temp_f:
        temp_f.write(content)

    pandoc_command = (
        f'pandoc -f markdown "{temp_md_file}" --lua-filter=remove-header-attr.lua'
        f' --wrap=preserve -o "{org_file}"'
    )
    os.system(pandoc_command)

    os.remove(temp_md_file)  # Clean up temp file

    # Add Org-roam header
    with open(org_file, "r+") as f:
        content = f.read()
        header = generate_org_roam_header(org_file, tags)
        content = header + content
        f.seek(0)
        f.write(content)
        f.truncate()

    print(f"Converted {md_file} to {org_file}")

def main():
    input_path = sys.argv[1]
    out_dir = "out/"

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            relative_path = os.path.relpath(root, input_path)
            for file in files:
                if file.endswith(".md"):
                    md_file = os.path.join(root, file)
                    convert_file(md_file, out_dir, relative_path)
    elif os.path.isfile(input_path) and input_path.endswith(".md"):
        convert_file(input_path, out_dir, "")
    else:
        print("Please provide a valid Markdown file or directory.")

if __name__ == "__main__":
    main()

