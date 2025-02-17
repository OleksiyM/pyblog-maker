import os
import re
import sys
import shutil
import markdown
import datetime
import zipfile
import argparse
from jinja2 import Environment, FileSystemLoader
from config import BLOG_TITLE, AUTHOR, SITE_URL, OUTPUT_DIR_FORMAT, POSTS_PER_PAGE, RECENT_POSTS_COUNT, TOP_CATEGORIES_COUNT, GA_TRACKING_ID
from typing import List, Dict, Tuple

# --- Helper Functions ---

def load_markdown_post(filepath: str) -> Dict:
    """Loads a Markdown post, parses metadata and content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    metadata_match = re.match(r'^(.*?)\n\n', content, re.DOTALL)
    if not metadata_match:
        raise ValueError(f"Invalid post format (no metadata): {filepath}")

    metadata_str = metadata_match.group(1)
    content_body = content[metadata_match.end():]

    def split_safe(s: str) -> List[str]:
        if not s:
            return []
        return [part.strip() for part in re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', s)]

    metadata = {}
    for line in metadata_str.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key in ("categories", "keywords", "tags"):
                value = split_safe(value)
            metadata[key] = value

    # Check for mandatory fields
    mandatory_fields = ['title', 'date', 'tags', 'description']
    missing_fields = [field for field in mandatory_fields if field not in metadata]
    if missing_fields:
        raise ValueError(f"Missing mandatory fields in {filepath}: {', '.join(missing_fields)}")

    # Validate non-empty fields
    empty_fields = [field for field in mandatory_fields if not metadata.get(field)]
    if empty_fields:
        raise ValueError(f"Empty mandatory fields in {filepath}: {', '.join(empty_fields)}")

    # Validate tags is not empty list
    if not metadata['tags']:
        raise ValueError(f"Tags list cannot be empty in {filepath}")

    try:
        metadata['date'] = datetime.datetime.strptime(metadata['date'], '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format in {filepath}. Use YYYY-MM-DD.")

    metadata['draft'] = metadata.get('draft', 'false').lower() == 'true'
    
    # Configure markdown with fenced code blocks and syntax highlighting
    md = markdown.Markdown(extensions=[
        'fenced_code',  # Enable ```language code blocks
        'codehilite',  # Enable syntax highlighting
        'tables',      # Enable tables
        'nl2br'        # Convert newlines to line breaks
    ])
    
    # Process the markdown content
    html_content = md.convert(content_body)
    
    # Replace code blocks with Prism.js compatible format
    html_content = re.sub(
        r'<div class="codehilite"><pre><code>(.*?)</code></pre></div>',
        r'<pre><code class="language-plaintext">\1</code></pre>',
        html_content,
        flags=re.DOTALL
    )
    
    # Add language classes for specific code blocks
    html_content = re.sub(
        r'<pre><code>([^<]*?)```(\w+)\n([^<]*?)```([^<]*?)</code></pre>',
        r'<pre><code class="language-\2">\3</code></pre>',
        html_content,
        flags=re.DOTALL
    )
    
    metadata['content'] = html_content
    metadata['filepath'] = filepath
    metadata['filename'] = os.path.basename(filepath).replace(".md","")

    return metadata


def generate_post_url(post: Dict) -> str:
    """Generates the URL for a post."""
    date_str = post['date'].strftime("%Y-%m-%d")
    title = post.get('title', '').lower().replace(" ", "-")
    title = re.sub(r'[^\w-]', '', title)

    if 'filename' in post:
        return f"posts/{post['filename']}.html"
    else:
        return f"posts/{date_str}-{title}.html"


def generate_category_url(category: str) -> str:
    """Generates the URL for a category page."""
    return f"categories/{category.lower().replace(' ', '-')}/"

def generate_tag_url(tag: str) -> str:
    """Generates the URL for a tag page."""
    return f"tags/{tag.lower().replace(' ', '-')}/"



def render_template(template_name: str, context: Dict, output_dir: str, output_filename: str, blog_name: str):
    """Renders a Jinja2 template and saves it."""
    template_path = os.path.join(blog_name, 'templates', 'default')
    env = Environment(loader=FileSystemLoader(template_path))

    # Add helper functions and current year to the context
    context.update({
        'generate_post_url': generate_post_url,
        'generate_category_url': generate_category_url,
        'generate_tag_url': generate_tag_url,
        'current_year': datetime.datetime.now().year  # Add current year
    })

    template = env.get_template(template_name)
    output_path = os.path.join(output_dir, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template.render(context))

def create_build_report(posts: List[Dict], output_dir: str, build_time: float, categories: Dict, tags: Dict):
    """Generates a build report."""
    report = {
        'build_time': build_time,
        'total_posts': len(posts),
        'total_categories': len(categories),
        'total_tags': len(tags),
        'date_generated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    report_str = f"""
    Build Report:
    -------------
    Build Time: {report['build_time']:.2f} seconds
    Total Posts: {report['total_posts']}
    Total Categories: {report['total_categories']}
    Total Tags: {report['total_tags']}
    Date Generated: {report['date_generated']}
    """

    with open(os.path.join(output_dir, "build_report.txt"), 'w', encoding='utf-8') as f:
        f.write(report_str)



def generate_static_pages(posts: List[Dict], output_dir: str, categories: Dict, tags: Dict, blog_name: str):
    """Generates all static pages (main, category, tag, etc.)."""

    # --- Main Page ---
    num_pages = (len(posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    for page_num in range(num_pages):
        start_index = page_num * POSTS_PER_PAGE
        end_index = start_index + POSTS_PER_PAGE
        paginated_posts = posts[start_index:end_index]

        context = {
            'blog_title': BLOG_TITLE,
            'posts': paginated_posts,
            'recent_posts': posts[:RECENT_POSTS_COUNT],
            'categories': sorted(categories.items(), key=lambda item: len(item[1]), reverse=True)[:TOP_CATEGORIES_COUNT],
            'tags': sorted(tags.items(), key=lambda item: len(item[1]), reverse=True),
            'current_page': page_num + 1,

            'num_pages': num_pages,
            'SITE_URL': SITE_URL
        }

        if page_num == 0:
            render_template('main.html', context, output_dir, 'index.html', blog_name)
        else:
            render_template('main.html', context, output_dir, f'page{page_num + 1}.html', blog_name)

    # --- Category Pages ---
    for category, category_posts in categories.items():
        context = {
            'blog_title': f"Category: {category}",
            'category': category,
            'posts': category_posts,
            'SITE_URL': SITE_URL,
            'num_pages': 1,  # Add this line
            'current_page': 1  # Add this line
        }
        render_template('main.html', context, output_dir, generate_category_url(category) + "index.html", blog_name)

    # --- Tag Pages ---
    for tag, tag_posts in tags.items():
        context = {
            'blog_title': f"Tag: {tag}",
            'tag': tag,
            'posts': tag_posts,
            'SITE_URL': SITE_URL,
            'num_pages': 1,  # Add this line
            'current_page': 1  # Add this line
        }
        render_template('main.html', context, output_dir, generate_tag_url(tag) + "index.html", blog_name)

    # --- 404 Page ---
    context = {
        'blog_title': "Page Not Found",
        'SITE_URL': SITE_URL
    }
    render_template('404.html', context, output_dir, '404.html', blog_name)


def generate_seo_files(output_dir: str, posts: List[Dict]):
    """Generates robots.txt, sitemap.xml, rss.xml, and atom.xml."""

    with open(os.path.join(output_dir, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write("User-agent: *\nDisallow:\nSitemap: " + SITE_URL + "/sitemap.xml")

    sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""

    sitemap_content += f"\n  <url><loc>{SITE_URL}/</loc></url>"
    for category in set(c for post in posts for c in post.get('categories',[])):
        sitemap_content += f"\n  <url><loc>{SITE_URL}/{generate_category_url(category)}</loc></url>"
    for tag in set(t for post in posts for t in post.get('tags',[])):
        sitemap_content += f"\n  <url><loc>{SITE_URL}/{generate_tag_url(tag)}</loc></url>"

    for post in posts:
            post_url = f"{SITE_URL}/{generate_post_url(post)}"
            lastmod = post['date'].strftime('%Y-%m-%d')
            sitemap_content += f"""
      <url>
        <loc>{post_url}</loc>
        <lastmod>{lastmod}</lastmod>
      </url>"""
    sitemap_content += "\n</urlset>"
    with open(os.path.join(output_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap_content)


    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
      <title>{BLOG_TITLE}</title>
      <link>{SITE_URL}</link>
      <description>{BLOG_TITLE}</description>
      <atom:link href="{SITE_URL}/rss.xml" rel="self" type="application/rss+xml" />"""
    for post in posts:
          post_url = f"{SITE_URL}/{generate_post_url(post)}"
          rss_content += f"""
      <item>
          <title>{post['title']}</title>
          <link>{post_url}</link>
          <guid>{post_url}</guid>
          <pubDate>{post['date'].strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
          <description>{post['description']}</description>
      </item>"""
    rss_content += "\n</channel>\n</rss>"
    with open(os.path.join(output_dir, 'rss.xml'), 'w', encoding='utf-8') as f:
        f.write(rss_content)

    atom_content = f"""<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">

      <title>{BLOG_TITLE}</title>
      <link href="{SITE_URL}/"/>
      <updated>{datetime.datetime.now().isoformat()}</updated>
      <id>{SITE_URL}/</id>
      <author>
        <name>{AUTHOR}</name>
      </author>
      <link rel="self" href="{SITE_URL}/atom.xml"/>
    """

    for post in posts:
        post_url = f"{SITE_URL}/{generate_post_url(post)}"
        atom_content += f"""
      <entry>
        <title>{post['title']}</title>
        <link href="{post_url}"/>
        <id>{post_url}</id>
        <updated>{post['date'].isoformat()}</updated>
        <summary>{post['description']}</summary>
      </entry>"""
    atom_content += "\n</feed>"

    with open(os.path.join(output_dir, 'atom.xml'), 'w', encoding='utf-8') as f:
        f.write(atom_content)

def copy_static_assets(output_dir: str, blog_name: str):
    """Copies CSS, JS, and images."""
    static_src = os.path.join(blog_name, 'templates', 'default', 'static')
    static_dest = os.path.join(output_dir, 'static')

    if os.path.exists(static_dest):
        shutil.rmtree(static_dest)
    shutil.copytree(static_src, static_dest)

    images_src = os.path.join(blog_name, 'images')
    images_dest = os.path.join(output_dir, 'images')
    if os.path.exists(images_dest):
      shutil.rmtree(images_dest)
    shutil.copytree(images_src, images_dest)


def add_google_analytics(output_dir : str):
    """Adds Google Analytics."""
    if not GA_TRACKING_ID:
        return

    ga_code = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{GA_TRACKING_ID}');
</script>
"""

    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r+', encoding='utf-8') as f:
                    content = f.read()
                    if "</body>" in content:
                        content = content.replace("</body>", ga_code + "\n</body>")
                        f.seek(0)
                        f.write(content)
                        f.truncate()



def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="PyBlogMaker - Static Blog Generator")
    parser.add_argument("-n", "--name", required=True, help="Name of the blog")
    parser.add_argument("-t", "--theme", default="default", help="Theme to use (default: default)")
    args = parser.parse_args()

    blog_name = args.name
    theme = args.theme

    start_time = datetime.datetime.now()

    posts_dir = os.path.join(blog_name, 'posts')
    if not os.path.isdir(posts_dir):
        print(f"Error: Posts directory '{posts_dir}' not found.")
        sys.exit(1)

    posts = []
    categories: Dict[str, List[Dict]] = {}
    tags: Dict[str, List[Dict]] = {}
    for filename in os.listdir(posts_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(posts_dir, filename)
            try:
                post = load_markdown_post(filepath)
                if not post['draft']:
                  posts.append(post)

                  for category in post.get('categories', []):
                      if category not in categories:
                          categories[category] = []
                      categories[category].append(post)

                  for tag in post.get('tags', []):
                      if tag not in tags:
                          tags[tag] = []
                      tags[tag].append(post)

            except ValueError as e:
                print(f"Error processing {filename}: {e}")

    posts.sort(key=lambda x: x['date'], reverse=True)

    output_dir_base = os.path.join(blog_name, 'dist')
    timestamp = datetime.datetime.now().strftime(OUTPUT_DIR_FORMAT)
    output_dir = os.path.join(output_dir_base, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    for post in posts:
         context = {
             'post': post,
             'blog_title': post['title'],
             'SITE_URL': SITE_URL
         }
         output_filename = generate_post_url(post)
         render_template('post.html', context, output_dir, output_filename, blog_name)

    generate_static_pages(posts, output_dir, categories, tags, blog_name)
    copy_static_assets(output_dir, blog_name)
    generate_seo_files(output_dir, posts)
    add_google_analytics(output_dir)
    end_time = datetime.datetime.now()
    build_time = (end_time - start_time).total_seconds()
    create_build_report(posts, output_dir, build_time, categories, tags)

    zip_filename = os.path.join(output_dir_base, f"{timestamp}.zip")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file),
                                           os.path.join(output_dir, '..')))
    print(f"Blog generated successfully in: {output_dir}")
    print(f"ZIP archive created: {zip_filename}")

if __name__ == "__main__":
    main()
