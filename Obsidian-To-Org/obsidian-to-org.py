import sys
import re
import os

def replace(pattern, substitution, filename):
    with open(filename, "r+") as f:
        content = f.read()
        content = re.sub(pattern, substitution, content)
        f.seek(0)
        f.write(content)
        f.truncate()

def extract_and_convert_tags(content):
    """Extract Obsidian-style tags block and convert them to Org-mode file tags."""
    tags_block_pattern = re.compile(r"tags:\s*(-\s+\w+\s*)+")
    tag_pattern = re.compile(r"-\s+(\S+)")

    filetags = ""
    def transform_tags_block(match):
        nonlocal filetags
        tags_block = match.group(0)
        tag_list = tag_pattern.findall(tags_block)
        filetags = "#+FILETAGS: " + " ".join([f":{tag}:" for tag in tag_list])
        return ""  # Remove the matched block from the content

    content = re.sub(tags_block_pattern, transform_tags_block, content)
    return content, filetags

def remove_md_header(content):
    """Remove Markdown header lines (starting and ending with ---)."""
    md_header_pattern = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
    return re.sub(md_header_pattern, "", content)

def convert_links(content):
    """Convert Obsidian-style links to Org-mode links."""
    link_pattern = re.compile(r"\[\[(.*?)(?:#(.*?))?(?:\|(.*?))?\]\]")

    def transform_link(match):
        target = match.group(1)  # File name or target
        subheading = match.group(2)  # Subheading or anchor
        alias = match.group(3)  # Link alias

        org_link = f"[[{target}]]"
        if subheading:
            org_link = f"[[{target}::{subheading}]]"
        if alias:
            org_link = f"[[{target}::{subheading}][{alias}]]" if subheading else f"[[{target}][{alias}]]"
        return org_link

    return re.sub(link_pattern, transform_link, content)

def convert_file(md_file, out_dir, relative_path):
    target_dir = os.path.join(out_dir, relative_path)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    org_file = os.path.splitext(md_file)[0] + ".org"
    org_file = os.path.join(target_dir, os.path.basename(org_file))

    with open(md_file, "r") as f:
        content = f.read()

    # Extract and convert tags
    content, filetags = extract_and_convert_tags(content)

    # Remove Markdown header
    content = remove_md_header(content)

    # Convert links
    content = convert_links(content)

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

    # Add Org-mode file tags
    with open(org_file, "r+") as f:
        content = f.read()
        content = filetags + "\n\n" + content if filetags else content
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
