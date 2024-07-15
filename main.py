import markdown
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def convert_md_to_html(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_content = markdown.markdown(md_content)

        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{os.path.splitext(os.path.basename(input_file))[0]}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        ensure_dir(output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)

        print(f"Conversion complete. HTML file saved as {output_file}")
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

class MarkdownHandler(FileSystemEventHandler):
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
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
        convert_md_to_html(self.input_file, self.output_file)

def watch_file(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: The input file '{input_file}' does not exist.")
        return

    event_handler = MarkdownHandler(input_file, output_file)
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
    output_file = os.path.join(script_dir, "docs", "index.html")
    
    if not os.path.exists(input_file):
        print(f"Error: The input file '{input_file}' does not exist.")
        print("Please ensure that 'Story.md' is in the 'src' directory.")
    else:
        ensure_dir(output_file)  # Ensure the build directory exists
        watch_file(input_file, output_file)