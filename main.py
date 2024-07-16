import markdown
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer
import re
import shutil
from bs4 import BeautifulSoup

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def split_content_into_pages(content, words_per_page=300):
    lines = content.split('\n')
    pages = []
    current_page = []
    word_count = 0

    for line in lines:
        words_in_line = len(re.findall(r'\S+', line))
        if word_count + words_in_line > words_per_page and current_page:
            pages.append('\n'.join(current_page))
            current_page = []
            word_count = 0

        current_page.append(line)
        word_count += words_in_line

        if line.strip() == '' and word_count >= words_per_page:
            pages.append('\n'.join(current_page))
            current_page = []
            word_count = 0

    if current_page:
        pages.append('\n'.join(current_page))

    return pages

def copy_images(src_dir, dest_dir):
    print(f"Copying images from {src_dir} to {dest_dir}")
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    copied_files = []
    for img in os.listdir(src_dir):
        if img.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            src_path = os.path.join(src_dir, img)
            dest_path = os.path.join(dest_dir, img)
            shutil.copy2(src_path, dest_path)
            copied_files.append(img)
            print(f"Copied {img} to {dest_path}")
    return copied_files

def extract_chapter_titles_and_locations(pages):
    chapter_info = []
    for i, page_content in enumerate(pages, start=1):
        soup = BeautifulSoup(markdown.markdown(page_content), 'html.parser')
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for heading in headings:
            chapter_info.append((heading.text.strip(), i))
    return chapter_info

def create_navigation_html(chapter_info):
    nav_html = '<nav id="chapter-nav"><ul>'
    for title, page_num in chapter_info:
        nav_html += f'<li><a href="{page_num}.html">{title}</a></li>'
    nav_html += '</ul></nav>'
    return nav_html

def convert_md_to_html_pages(input_file, output_dir):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        pages = split_content_into_pages(md_content)
        chapter_info = extract_chapter_titles_and_locations(pages)
        navigation_html = create_navigation_html(chapter_info)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_img_dir = os.path.join(script_dir, "src", "images")
        dest_img_dir = os.path.join(output_dir, "images")
        copied_images = copy_images(src_img_dir, dest_img_dir)

        for i, page_content in enumerate(pages, start=1):
            html_content = markdown.markdown(page_content, extensions=['extra'])

            # Process image links in the markdown content
            soup = BeautifulSoup(html_content, 'html.parser')
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and src.startswith('images/'):
                    img_filename = os.path.basename(src)
                    if img_filename in copied_images:
                        img['src'] = f"images/{img_filename}"
                        print(f"Updated image link for {img_filename} on page {i}")
                    else:
                        print(f"Warning: Image {img_filename} referenced but not found in the images directory")

            html_content = str(soup)

            # Add id attributes to headings
            soup = BeautifulSoup(html_content, 'html.parser')
            for j, heading in enumerate(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']), start=1):
                heading['id'] = f"heading-{j}"
            html_content = str(soup)

            html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page {i}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.6;
            color: #000;
            background-color: #fff;
            margin: 0;
            padding: 0;
            display: flex;
        }}
        #chapter-nav {{
            width: 250px;
            height: 100vh;
            overflow-y: auto;
            position: sticky;
            top: 0;
            background-color: #f4f4f4;
            padding: 1rem;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        }}
        #chapter-nav ul {{
            list-style-type: none;
            padding: 0;
        }}
        #chapter-nav li {{
            margin-bottom: 0.5rem;
        }}
        #chapter-nav a {{
            text-decoration: none;
            color: #333;
        }}
        #chapter-nav a:hover {{
            text-decoration: underline;
        }}
        main {{
            flex-grow: 1;
            max-width: 600px;
            width: 90%;
            margin: 2rem auto;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        p {{
            margin-bottom: 1em;
        }}
        img {{
          max-width: 100%;
          height: auto;
        }}
        .chapter-content {{
            margin-bottom: 2rem;
        }}
        .navigation-buttons {{
            display: flex;
            justify-content: space-between;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #000;
        }}
        .btn {{
            background-color: #fff;
            color: #000;
            border: 1px solid #000;
            padding: 0.5rem 1rem;
            text-decoration: none;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        .btn:hover {{
            background-color: #000;
            color: #fff;
        }}
        footer {{
            text-align: center;
            padding: 1rem;
            font-size: 0.8rem;
            border-top: 1px solid #000;
        }}
        @media (max-width: 768px) {{
            body {{
                flex-direction: column;
            }}
            #chapter-nav {{
                width: 100%;
                height: auto;
                position: static;
            }}
            main {{
                width: 95%;
            }}
        }}
    </style>
</head>
<body>
    {navigation_html}
    <main>
        <article class="chapter-content">
            {html_content}
        </article>
        <div class="navigation-buttons">
            <a href="{i-1}.html" class="btn" {'style="visibility: hidden;"' if i == 1 else ''}>Previous Page</a>
            <a href="{i+1}.html" class="btn" {'style="visibility: hidden;"' if i == len(pages) else ''}>Next Page</a>
        </div>
    </main>
    <footer>
        <p>Page {i} | The Ritual of Preservation! &copy; 2024</p>
    </footer>
</body>
</html>
            """

            output_file = os.path.join(output_dir, f"{i}.html")
            ensure_dir(output_file)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_template)

        print(f"Conversion complete. HTML files saved in {output_dir}")
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

class MarkdownHandler(FileSystemEventHandler):
    def __init__(self, input_file, output_dir):
        self.input_file = input_file
        self.output_dir = output_dir
        self.timer = None

    def on_modified(self, event):
        if event.src_path == self.input_file:
            print(f"\nFile {self.input_file} has been modified. Queuing conversion...")
            self.queue_conversion()

    def queue_conversion(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = Timer(10.0, self.perform_conversion)
        self.timer.start()

    def perform_conversion(self):
        print("Processing queued conversion...")
        convert_md_to_html_pages(self.input_file, self.output_dir)

def watch_file(input_file, output_dir):
    if not os.path.exists(input_file):
        print(f"Error: The input file '{input_file}' does not exist.")
        return

    event_handler = MarkdownHandler(input_file, output_dir)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(input_file), recursive=False)
    
    try:
        observer.start()
        print(f"Watching {input_file} for changes. Press Ctrl+C to stop.")
        print("Conversions will be processed 10 seconds after the last save.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        observer.join()

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "src", "Story.md")
    output_dir = os.path.join(script_dir, "docs")
    
    if not os.path.exists(input_file):
        print(f"Error: The input file '{input_file}' does not exist.")
        print("Please ensure that 'Story.md' is in the 'src' directory.")
    else:
        ensure_dir(output_dir)  # Ensure the docs directory exists
        convert_md_to_html_pages(input_file, output_dir)  # Perform initial conversion
        watch_file(input_file, output_dir)