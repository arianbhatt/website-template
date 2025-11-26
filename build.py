import os
import re
import markdown
import yaml
from datetime import datetime

# --- Configuration ---
POSTS_DIR = 'posts'
OUTPUT_DIR = '.' # Output HTML files to the root directory
INDEX_TEMPLATE_FILE = 'index.html'
BLOG_STYLESHEET = '<link rel="stylesheet" href="style.css">'
PLACEHOLDER = '<!-- POSTS_LIST_INSERT -->'

# --- HTML Templates ---

# Template for the individual blog post HTML page
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {stylesheet}
</head>
<body>
    <main>
        <p><a href="index.html">← Back to Home</a></p>

        <header class="post-header">
            <h1>{title}</h1>
            <time datetime="{date_iso}">Published on {date_formatted}</time>
        </header>

        <article class="post-content">
            {content}
        </article>
        
        <footer class="footer">
            <a href="index.html">← Back to All Posts</a>
        </footer>
    </main>
</body>
</html>"""

# Template for a single post link item in index.html
POST_LINK_ITEM = """
            <article class="post-item">
                <a href="{filename}.html" class="post-item-link">
                    <div class="post-item-title">{title}</div>
                    <time class="post-item-date" datetime="{date_iso}">{date_formatted}</time>
                </a>
            </article>"""

def parse_markdown_file(filepath):
    """Reads a Markdown file, separates front matter from content, and parses metadata."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Use regex to find the YAML front matter block (if present)
    match = re.match(r'---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    
    if match:
        front_matter = match.group(1)
        md_content = content[match.end():]
        metadata = yaml.safe_load(front_matter)
    else:
        # Fallback if no front matter
        md_content = content
        metadata = {'title': os.path.basename(filepath).replace('.md', '').replace('-', ' ').title(), 'date': '1970-01-01'}

    # Ensure title and date are present
    if not metadata.get('title'):
        metadata['title'] = "Untitled Post"
    if not metadata.get('date'):
        metadata['date'] = '1970-01-01'
        
    return metadata, md_content

def build_post_page(metadata, md_content, filename_base):
    """Converts Markdown content to HTML and wraps it in the post template."""
    # Convert Markdown to HTML
    html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
    
    # Format dates
    date_obj = datetime.strptime(str(metadata['date']), '%Y-%m-%d')
    date_iso = date_obj.strftime('%Y-%m-%d')
    date_formatted = date_obj.strftime('%B %d, %Y')

    # Fill the post template
    final_html = POST_TEMPLATE.format(
        title=metadata['title'],
        date_iso=date_iso,
        date_formatted=date_formatted,
        content=html_content,
        stylesheet=BLOG_STYLESHEET
    )

    # Write the output file
    output_path = os.path.join(OUTPUT_DIR, f"{filename_base}.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f"-> Generated post: {output_path}")

    # Return data needed for the index page
    return {
        'title': metadata['title'],
        'date': date_obj,
        'date_iso': date_iso,
        'date_formatted': date_formatted,
        'filename': filename_base
    }

def build_index_page(post_data_list):
    """Generates the main index.html file with a sorted list of all posts."""
    
    # Sort posts by date, descending (latest first)
    post_data_list.sort(key=lambda x: x['date'], reverse=True)
    
    # Generate the HTML list of links
    post_links_html = ""
    for post in post_data_list:
        post_links_html += POST_LINK_ITEM.format(
            title=post['title'],
            date_iso=post['date_iso'],
            date_formatted=post['date_formatted'],
            filename=post['filename']
        )

    # Read the index template
    with open(INDEX_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        index_template = f.read()

    # Insert the generated list into the template
    final_index_html = index_template.replace(PLACEHOLDER, post_links_html)

    # Write the final index.html
    with open(INDEX_TEMPLATE_FILE, 'w', encoding='utf-8') as f:
        f.write(final_index_html)
        
    print(f"-> Updated index file: {INDEX_TEMPLATE_FILE}")


def main():
    print("--- Starting Blog Build Process ---")
    
    if not os.path.exists(POSTS_DIR):
        print(f"Error: '{POSTS_DIR}/' directory not found. Please create it.")
        return

    all_posts_data = []

    # 1. Process all markdown files
    for filename in os.listdir(POSTS_DIR):
        if filename.endswith(".md"):
            filepath = os.path.join(POSTS_DIR, filename)
            filename_base = filename.replace('.md', '')
            
            # Parse and build individual post HTML
            metadata, md_content = parse_markdown_file(filepath)
            post_data = build_post_page(metadata, md_content, filename_base)
            all_posts_data.append(post_data)

    # 2. Build the index page with the list of all posts
    if all_posts_data:
        build_index_page(all_posts_data)
    else:
        print("Warning: No markdown files found to process.")

    print("--- Build Process Complete ---")

if __name__ == "__main__":
    # Ensure dependencies are available (though this is run in GH Actions)
    try:
        main()
    except Exception as e:
        print(f"A fatal error occurred during build: {e}")
        # Exit with a non-zero status code to fail the CI build
        exit(1)
