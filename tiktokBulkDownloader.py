import os
import sys
import subprocess
import re
import json
import csv
from datetime import datetime
import signal

# Global variable to track metadata during script execution
downloaded_metadata = []

# Global variable to prevent multiple retries
retry_attempted = False

def signal_handler(signal_received, frame):
    """
    Handle interruption signals (e.g., Ctrl-C).
    Save the downloaded metadata to the CSV file before exiting.
    """
    if downloaded_metadata:
        print("\nScript interrupted! Saving metadata for downloaded videos...")
        save_metadata_to_csv()
    print("Exiting gracefully.")
    sys.exit(0)

def save_metadata_to_csv():
    """
    Save the downloaded metadata to a CSV file.
    """
    if not downloaded_metadata:
        return  # No metadata to save

    # Create a timestamped CSV filename
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    csv_file = f"{current_time}_download_log.csv"

    # Save metadata to the CSV file
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Upload Date", "Uploader", "Title", "URL", "Filename", "Duration (sec)", "View Count", "Like Count", "Comment Count", "Repost Count", "Resolution"])
        writer.writerows(downloaded_metadata)

def clean_links_file(input_file):
    """
    Cleans the input links file by removing extraneous lines and prefixes, leaving only a pure list of links.
    Returns the cleaned list of links.

    :param input_file: Path to the input file
    :type input_file: str
    :return: List of cleaned links
    :rtype: list[str]
    """
    cleaned_links = []
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                # Skip blank lines and lines starting with "Date:"
                if not line or line.startswith("Date:"):
                    continue
                # Remove "Link: " prefix if present
                if line.startswith("Link: "):
                    line = line.replace("Link: ", "")
                # Add the cleaned link to the list
                cleaned_links.append(line)
    except Exception as e:
        print(f"Error reading or cleaning the input file: {e}")
    return cleaned_links

def get_simple_variable_mapping():
    """
    Returns a mapping of simple human-readable variable names to yt-dlp template variables.
    """
    return {
        # Basic metadata
        'title': '%(title).180B',
        'creator': '%(uploader).50s',
        'description': '%(description).100s',

        # IDs
        'videoid': '%(id)s',
        'videoID': '%(id)s',  # Accept both cases
        'creatorid': '%(uploader_id)s',
        'creatorID': '%(uploader_id)s',  # Accept both cases

        # Dates
        'date': '%(upload_date>%Y-%m-%d)s',
        'year': '%(upload_date>%Y)s',
        'month': '%(upload_date>%m)s',
        'day': '%(upload_date>%d)s',
        'shortdate': '%(upload_date>%y%m%d)s',
        'fulldate': '%(upload_date)s',

        # Statistics
        'views': '%(view_count)s',
        'likes': '%(like_count)s',
        'comments': '%(comment_count)s',
        'shares': '%(repost_count)s',

        # Video properties
        'duration': '%(duration)s',
        'resolution': '%(resolution)s',
        'fps': '%(fps)s',
        'format': '%(format_id)s',

        # Platform
        'platform': '%(extractor)s',

        # File extension (always required)
        'ext': '%(ext)s'
    }

def build_custom_filename_template(variables):
    """
    Builds a yt-dlp filename template from a list of simple variable names.

    :param variables: List of simple variable names from the user
    :type variables: list[str]
    :return: yt-dlp filename template string
    :rtype: str
    """
    mapping = get_simple_variable_mapping()
    template_parts = []

    for var in variables:
        var_lower = var.lower()
        if var_lower in mapping:
            template_parts.append(mapping[var_lower])
        else:
            # If not a recognized variable, treat it as literal text
            template_parts.append(var)

    # Join parts with underscores
    template = '_'.join(template_parts)

    # Always ensure .ext is at the end if not already included
    if '%(ext)s' not in template:
        template += '.%(ext)s'

    return template

def get_filename_template(args):
    """
    Determines the filename template based on command line arguments.

    :param args: Dictionary of parsed command line arguments
    :type args: dict
    :return: yt-dlp filename template string
    :rtype: str
    """
    # Predefined filename format presets
    presets = {
        'default': "%(upload_date).10s_%(uploader).50s_%(title).180B.%(ext)s",
        'no-date': "%(uploader).50s_%(title).180B.%(ext)s",
        'title-only': "%(title).200B.%(ext)s",
        'creator-id': "%(uploader)s_%(id)s.%(ext)s",
        'date-title': "%(upload_date)s_%(title).150B.%(ext)s",
        'clean': "%(uploader)s_%(title).100s.%(ext)s"
    }

    # Priority order: filename_custom > custom template > specific flags > preset > default

    # New filename_custom takes highest priority
    if args.get('filename_custom'):
        return build_custom_filename_template(args['filename_custom'])

    # Custom template takes next priority
    if args.get('custom_template'):
        return args['custom_template']

    # Specific convenience flags
    if args.get('no_date'):
        return presets['no-date']
    elif args.get('title_only'):
        return presets['title-only']
    elif args.get('creator_id'):
        return presets['creator-id']

    # Preset selection
    if args.get('filename_preset'):
        preset_name = args['filename_preset']
        if preset_name in presets:
            return presets[preset_name]
        else:
            print(f"Warning: Unknown preset '{preset_name}'. Using default format.")
            return presets['default']

    # Default fallback
    return presets['default']

def validate_filename_template(template):
    """
    Validates that a filename template contains required yt-dlp format specifiers.

    :param template: yt-dlp filename template string
    :type template: str
    :return: True if valid, False otherwise
    :rtype: bool
    """
    # Must contain %(ext)s for file extension
    if "%(ext)s" not in template:
        print("Error: Filename template must contain %(ext)s for file extension")
        return False

    # Should contain at least one content identifier
    content_ids = ["%(title)", "%(uploader)", "%(id)", "%(upload_date)"]
    if not any(content_id in template for content_id in content_ids):
        print("Warning: Template should contain at least one of: %(title), %(uploader), %(id), %(upload_date)")

    return True

def list_filename_presets():
    """
    Prints all available filename presets with examples.
    """
    presets = {
        'default': ("%(upload_date).10s_%(uploader).50s_%(title).180B.%(ext)s", "20220607_creator_video_title.mp4"),
        'no-date': ("%(uploader).50s_%(title).180B.%(ext)s", "creator_video_title.mp4"),
        'title-only': ("%(title).200B.%(ext)s", "video_title.mp4"),
        'creator-id': ("%(uploader)s_%(id)s.%(ext)s", "creator_7106594312292453675.mp4"),
        'date-title': ("%(upload_date)s_%(title).150B.%(ext)s", "20220607_video_title.mp4"),
        'clean': ("%(uploader)s_%(title).100s.%(ext)s", "creator_video_title.mp4")
    }

    print("Available filename presets:")
    print("-" * 50)
    for name, (template, example) in presets.items():
        print(f"{name:12} - {example}")
    print("-" * 50)
    print("Usage: --filename-preset <preset_name>")

def list_simple_variables():
    """
    Prints all available simple variable names for --filename-custom.
    """
    mapping = get_simple_variable_mapping()

    print("\nAvailable Variables for --filename-custom:")
    print("=" * 60)

    categories = {
        'Basic Info': ['title', 'creator', 'description'],
        'IDs': ['videoID', 'creatorID'],
        'Dates': ['date', 'year', 'month', 'day', 'shortdate', 'fulldate'],
        'Statistics': ['views', 'likes', 'comments', 'shares'],
        'Video Properties': ['duration', 'resolution', 'fps', 'format'],
        'Other': ['platform', 'ext']
    }

    for category, vars in categories.items():
        print(f"\n{category}:")
        for var in vars:
            if var == 'date':
                example = "2024-12-07"
            elif var == 'shortdate':
                example = "241207"
            elif var == 'fulldate':
                example = "20241207"
            elif var == 'year':
                example = "2024"
            elif var == 'month':
                example = "12"
            elif var == 'day':
                example = "07"
            elif var == 'videoID':
                example = "7106594312292453675"
            elif var == 'creatorID':
                example = "username123"
            else:
                example = var
            print(f"  {var:15} → {example}")

    print("\n" + "=" * 60)
    print("Usage: --filename-custom [var1] [var2] [var3] ...")
    print("Example: --filename-custom date creator title")
    print("Result: 2024-12-07_username_video_title.mp4")
    print("\nNote: Variables are joined with underscores by default.")

def show_help():
    """
    Displays comprehensive help information for all script options.
    """
    help_text = """
TikTok Bulk Downloader - User-Friendly Filename Customization

USAGE:
    python3 tiktokBulkDownloader.py [OPTIONS]

BASIC OPTIONS:
    --cookies              Use cookies.txt for private/restricted videos
    --links <file/url>     Specify input file or single URL (default: links.txt)
    --watermark            Download watermarked versions (lower quality)

FILENAME OPTIONS (choose one):
    --no-date             Remove date: creator - title.mp4
    --title-only          Title only: title.mp4
    --creator-id          Creator + ID: creator_7106594312292453675.mp4
    --filename-preset <name>  Use predefined format (see --list-presets)
    --filename-custom [var1] [var2]...  Build filename from simple variables (see --list-variables)
    --filename-yt-dlp "template"  Use yt-dlp template syntax (advanced users)

HELP & UTILITIES:
    --help                Show this help message
    --list-presets        Show all available filename presets
    --list-variables      Show all available variables for --filename-custom
    --preview-filename <url>  Preview filename format without downloading

EXAMPLES:
    # Basic usage
    python3 tiktokBulkDownloader.py

    # Remove dates from filenames
    python3 tiktokBulkDownloader.py --no-date

    # Download single video with custom format
    python3 tiktokBulkDownloader.py --title-only --links "https://tiktok.com/@user/video/123"

    # Use preset format with cookies
    python3 tiktokBulkDownloader.py --filename-preset creator-id --cookies

    # Use simple variables to build custom filename
    python3 tiktokBulkDownloader.py --filename-custom date creator videoID

    # Advanced yt-dlp template (for experienced users)
    python3 tiktokBulkDownloader.py --filename-yt-dlp "%(uploader)s_%(upload_date)s.%(ext)s"

FILENAME FORMAT NOTES:
    - Default: 2022-06-07 - creator - video title.mp4
    - All formats automatically handle special characters and length limits
    - Custom templates use yt-dlp format specifiers (%(title)s, %(uploader)s, etc.)
    """
    print(help_text)

def show_filename_preview(url, args):
    """
    Shows what the filename would look like for a given URL with specified format options.

    :param url: TikTok video URL to preview
    :type url: str
    :param args: Dictionary of filename format arguments
    :type args: dict
    """
    try:
        print(f"Fetching metadata for: {url}")
        print("This may take a moment...")

        # Use yt-dlp to get metadata without downloading
        cmd_metadata = ["yt-dlp", "--dump-json", "--no-warnings", url]

        result = subprocess.run(
            cmd_metadata,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"Error: Could not fetch metadata for this URL")
            print(f"yt-dlp error: {result.stderr.strip()}")
            return

        # Parse JSON output
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print("Error: Could not parse video metadata")
            return

        # Get the filename template
        filename_template = get_filename_template(args)

        # Extract metadata
        upload_date = data.get("upload_date", "20220607")
        formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}" if upload_date else "2022-06-07"
        uploader = data.get("uploader", "unknown_creator")
        title = data.get("title", "Unknown Title")
        video_id = data.get("id", "1234567890")

        # Create a sample filename by manually substituting the template
        # This is a simplified version - yt-dlp does more sophisticated formatting
        sample_filename = filename_template.replace("%(upload_date).10s", formatted_date)
        sample_filename = sample_filename.replace("%(upload_date>%Y-%m-%d)s", formatted_date)
        sample_filename = sample_filename.replace("%(upload_date>%Y)s", upload_date[:4] if upload_date else "2024")
        sample_filename = sample_filename.replace("%(upload_date>%m)s", upload_date[4:6] if upload_date else "01")
        sample_filename = sample_filename.replace("%(upload_date>%d)s", upload_date[6:8] if upload_date else "01")
        sample_filename = sample_filename.replace("%(upload_date>%y%m%d)s", upload_date[2:] if upload_date else "240101")
        sample_filename = sample_filename.replace("%(upload_date)s", upload_date)
        sample_filename = sample_filename.replace("%(uploader).50s", uploader[:50])
        sample_filename = sample_filename.replace("%(uploader)s", uploader)
        sample_filename = sample_filename.replace("%(title).180B", title[:180])
        sample_filename = sample_filename.replace("%(title).200B", title[:200])
        sample_filename = sample_filename.replace("%(title).150B", title[:150])
        sample_filename = sample_filename.replace("%(title).100s", title[:100])
        sample_filename = sample_filename.replace("%(title)s", title)
        sample_filename = sample_filename.replace("%(id)s", video_id)
        sample_filename = sample_filename.replace("%(ext)s", "mp4")

        # Show results
        print("\n" + "="*60)
        print("FILENAME PREVIEW")
        print("="*60)
        print(f"Video: {title}")
        print(f"Creator: {uploader}")
        print(f"Upload Date: {formatted_date}")
        print(f"Video ID: {video_id}")
        print("-"*60)
        print(f"Template: {filename_template}")
        print(f"Result: {sample_filename}")
        print("="*60)

        # Show other format examples
        print("\nOther available formats:")
        other_formats = {
            'default': "%(upload_date).10s_%(uploader).50s_%(title).180B.%(ext)s",
            'no-date': "%(uploader).50s_%(title).180B.%(ext)s",
            'title-only': "%(title).200B.%(ext)s",
            'creator-id': "%(uploader)s_%(id)s.%(ext)s"
        }

        for name, template in other_formats.items():
            if template != filename_template:  # Don't show the current one again
                sample = template.replace("%(upload_date).10s", upload_date[:10])
                sample = sample.replace("%(uploader).50s", uploader[:50])
                sample = sample.replace("%(uploader)s", uploader)
                sample = sample.replace("%(title).180B", title[:180])
                sample = sample.replace("%(title).200B", title[:200])
                sample = sample.replace("%(id)s", video_id)
                sample = sample.replace("%(ext)s", "mp4")
                print(f"  --filename-preset {name:12} → {sample}")

    except subprocess.TimeoutExpired:
        print("Error: Request timed out. Check your internet connection and try again.")
    except Exception as e:
        print(f"Error: {e}")

def download_with_ytdlp(links, download_dir, use_cookies=False, use_watermark=False, filename_template=None):
    """
    Bulk-downloads a list of TikTok videos using yt-dlp and logs metadata.

    :param links: List of TikTok video URLs to download
    :type links: list[str]
    :param download_dir: Target directory to save the downloaded videos
    :type download_dir: str
    :param use_cookies: Whether to append --cookies cookies.txt to yt-dlp
                        commands for authenticated requests
    :type use_cookies: bool
    :param use_watermark: Whether to use the "download" format (watermarked videos).
                          Note: This downloads lower quality (576x1024) watermarked videos
                          instead of high quality (1080x1920) non-watermarked videos.
    :type use_watermark: bool
    :return: None
    """
    global retry_attempted
    print("Starting download_with_ytdlp function...")

    # Ensure the download directory exists, or attempt creation
    if not os.path.exists(download_dir):
        try:
            os.mkdir(download_dir)
            print(f"Created directory: {download_dir}")
        except Exception as e:
            print(f"Failed to create directory {download_dir}: {e}")
            return

    # Log file named by current date/time for recording failed downloads
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    failed_log_file = f"{current_time}_failed_downloads_log.txt"

    # Track success/failure statistics
    total_links = len(links)
    successful_downloads = 0
    failed_downloads = 0
    failed_links = []  # Collect links that fail for retry

    # Iterate through each link
    for index, link in enumerate(links, start=1):
        try:
            print()
            print(f"[{index}/{total_links}]: {link}")

            # Define yt-dlp output template (now user-customizable!)
            # Use the filename template passed as parameter or default format
            template_format = filename_template if filename_template else "%(upload_date).10s - %(uploader).50s - %(title).180B.%(ext)s"
            output_template = os.path.join(download_dir, template_format)

            # yt-dlp command for downloading the video
            cmd_download = [
                "yt-dlp",
                "--progress",
                "--no-warnings",
                "-o", output_template
            ]
            # Add watermark format if requested
            # Note: "download" format provides watermarked videos but at lower quality
            if use_watermark:
                cmd_download += ["--format", "download"]
            if use_cookies:
                cmd_download += ["--cookies", "cookies.txt"]
            cmd_download.append(link)

            print()
            subprocess.run(cmd_download, check=True)

            # Fetch metadata for logging
            cmd_metadata = ["yt-dlp", "--dump-json"]
            if use_cookies:
                cmd_metadata += ["--cookies", "cookies.txt"]
            cmd_metadata.append(link)

            result = subprocess.run(
                cmd_metadata,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise Exception(f"Failed to fetch metadata for {link}\n{result.stderr.strip()}")

            # Parse JSON output to extract metadata
            data = json.loads(result.stdout)

            # Extract and format the upload date
            upload_date = data.get("upload_date", "0000-00-00")
            formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}" if upload_date != "0000-00-00" else upload_date

            # Append metadata to the global list for logging
            downloaded_metadata.append([
                formatted_date,
                data.get("uploader", "unknown_uploader"),
                data.get("title", "Untitled"),
                link,
                f"{formatted_date} - {data.get('uploader', 'unknown_uploader')} - {data.get('title', 'Untitled')}",
                data.get("duration", ""),
                data.get("view_count", ""),
                data.get("like_count", ""),
                data.get("comment_count", ""),
                data.get("repost_count", ""),
                f"{data.get('height', '')}p" if data.get("height") else "",
            ])

            print(" SUCCESS")
            successful_downloads += 1

        except Exception as e:
            print(" FAILED")
            failed_downloads += 1
            failed_links.append(link)

            # Log the error details to the timestamped log file
            with open(failed_log_file, "a", encoding="utf-8") as f:
                f.write(f"{link}\nError: {str(e).strip()}\n{'-' * 40}\n")

    # Retry logic for failed links
    if failed_links and not retry_attempted:
        retry_attempted = True
        print(f"\nRe-attempting download for {len(failed_links)} failed links...\n")
        download_with_ytdlp(failed_links, download_dir, use_cookies=use_cookies, use_watermark=use_watermark, filename_template=filename_template)
    elif failed_links:
        print("\nSome downloads still failed after one retry. Check the failed downloads log for details.")
        with open(failed_log_file, "a", encoding="utf-8") as f:
            f.write("\nFailed links after retry:\n")
            for link in failed_links:
                f.write(f"{link}\n")

    # Final summary only printed once
    if not retry_attempted or not failed_links:
        save_metadata_to_csv()
        print("\nDownload process complete.")
        print(f"Successful downloads: {successful_downloads}/{total_links}")
        print(f"Failed downloads: {failed_downloads}/{total_links}")

def main():
    """
    Main entry point: reads user input, checks for cookies usage,
    validates arguments, loads input file (default or specified with --links),
    and calls the download function.
    """
    # Register signal handler for Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)

    # Recognized arguments
    valid_args = {
        "--cookies", "--links", "--watermark",
        # Filename customization options
        "--no-date", "--title-only", "--creator-id",
        "--filename-preset", "--filename-yt-dlp", "--filename-custom",
        # Help and utility options
        "--help", "--list-presets", "--list-variables", "--preview-filename"
    }
    provided_args = set(arg for arg in sys.argv[1:] if arg.startswith("-"))
    invalid_args = provided_args - valid_args

    # Check for invalid arguments
    if invalid_args:
        print(f"Error: Unrecognized argument(s): {', '.join(invalid_args)}")
        show_help()
        return

    # Handle help and utility commands first
    if "--help" in sys.argv:
        show_help()
        return

    if "--list-presets" in sys.argv:
        list_filename_presets()
        return

    if "--list-variables" in sys.argv:
        list_simple_variables()
        return

    # Parse filename preview request
    if "--preview-filename" in sys.argv:
        try:
            preview_index = sys.argv.index("--preview-filename") + 1
            if preview_index >= len(sys.argv):
                print("Error: --preview-filename requires a URL argument")
                return
            preview_url = sys.argv[preview_index]

            # Parse remaining args for filename options
            preview_args = {}
            preview_args['no_date'] = "--no-date" in sys.argv
            preview_args['title_only'] = "--title-only" in sys.argv
            preview_args['creator_id'] = "--creator-id" in sys.argv

            if "--filename-preset" in sys.argv:
                try:
                    preset_idx = sys.argv.index("--filename-preset") + 1
                    if preset_idx < len(sys.argv):
                        preview_args['filename_preset'] = sys.argv[preset_idx]
                except ValueError:
                    pass

            if "--filename-yt-dlp" in sys.argv:
                try:
                    template_idx = sys.argv.index("--filename-yt-dlp") + 1
                    if template_idx < len(sys.argv):
                        template = sys.argv[template_idx]
                        if validate_filename_template(template):
                            preview_args['custom_template'] = template
                except ValueError:
                    pass

            if "--filename-custom" in sys.argv:
                try:
                    custom_idx = sys.argv.index("--filename-custom") + 1
                    custom_vars = []
                    while custom_idx < len(sys.argv) and not sys.argv[custom_idx].startswith("--"):
                        custom_vars.append(sys.argv[custom_idx])
                        custom_idx += 1
                    if custom_vars:
                        preview_args['filename_custom'] = custom_vars
                except ValueError:
                    pass

            # Show filename preview
            show_filename_preview(preview_url, preview_args)
            return
        except (ValueError, IndexError):
            print("Error: --preview-filename requires a URL argument")
            return

    # Parse all arguments into a dictionary
    args = {}

    # Basic options
    args['use_cookies'] = "--cookies" in sys.argv
    args['use_watermark'] = "--watermark" in sys.argv

    # Filename customization options
    args['no_date'] = "--no-date" in sys.argv
    args['title_only'] = "--title-only" in sys.argv
    args['creator_id'] = "--creator-id" in sys.argv

    # Parse --filename-preset
    if "--filename-preset" in sys.argv:
        try:
            preset_index = sys.argv.index("--filename-preset") + 1
            if preset_index >= len(sys.argv):
                print("Error: --filename-preset requires a preset name")
                print("Use --list-presets to see available options")
                return
            args['filename_preset'] = sys.argv[preset_index]
        except ValueError:
            print("Error: --filename-preset requires a preset name")
            return

    # Parse --filename-yt-dlp
    if "--filename-yt-dlp" in sys.argv:
        try:
            template_index = sys.argv.index("--filename-yt-dlp") + 1
            if template_index >= len(sys.argv):
                print("Error: --filename-yt-dlp requires a template string")
                return
            custom_template = sys.argv[template_index]
            if not validate_filename_template(custom_template):
                return
            args['custom_template'] = custom_template
        except ValueError:
            print("Error: --filename-yt-dlp requires a template string")
            return

    # Parse --filename-custom
    if "--filename-custom" in sys.argv:
        try:
            custom_index = sys.argv.index("--filename-custom") + 1
            if custom_index >= len(sys.argv):
                print("Error: --filename-custom requires at least one variable")
                print("Use --list-variables to see available options")
                return
            custom_vars = []
            while custom_index < len(sys.argv) and not sys.argv[custom_index].startswith("--"):
                custom_vars.append(sys.argv[custom_index])
                custom_index += 1
            if not custom_vars:
                print("Error: --filename-custom requires at least one variable")
                print("Use --list-variables to see available options")
                return
            args['filename_custom'] = custom_vars
        except ValueError:
            print("Error: --filename-custom requires variables")
            return

    # Parse --links argument
    links_arg_index = sys.argv.index("--links") + 1 if "--links" in sys.argv else None
    use_cookies = args['use_cookies']
    use_watermark = args['use_watermark']

    # Validate links argument if provided
    links_arg = sys.argv[links_arg_index] if links_arg_index else "links.txt"
    links = []

    # Check if the --links argument contains a single URL or a file path
    if re.match(r'https?://', links_arg):
        # If the argument looks like a URL, treat it as a single link
        links = [links_arg.strip()]
    else:
        # Otherwise, assume it is a file path and validate the file
        if not os.path.exists(links_arg):
            print(f"Input file '{links_arg}' not found. Please create it and add your video links.")
            return
        # Clean the input file to extract only valid links
        links = clean_links_file(links_arg)

    # Ensure there are valid links to process
    if not links:
        print("No valid links found.")
        return

    # Prompt for directory to store downloads
    print("\nOutput Directory Options:")
    print("- Enter a folder name (e.g., 'my_videos') to create it in the current directory")
    print("- Enter a full path:")
    print("  • Mac/Linux: '/Users/name/Downloads/tiktoks' or '~/Downloads/tiktoks'")
    print("  • Windows: 'C:\\Users\\Name\\Downloads\\tiktoks' or '%USERPROFILE%\\Downloads\\tiktoks'")
    print("- Press Enter to save videos in the current directory")
    download_dir = input("\nEnter directory path or press Enter for current directory: ").strip()

    # Default to current directory if empty
    if not download_dir:
        download_dir = "."
        print("Using current directory for downloads")
    else:
        # Expand user home directory (~) and environment variables
        download_dir = os.path.expanduser(os.path.expandvars(download_dir))

    # Attempt to create the directory if it doesn't exist
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir, exist_ok=True)
            print(f"Created directory: {os.path.abspath(download_dir)}")
        except Exception as e:
            print(f"Failed to create directory {download_dir}: {e}")
            return
    else:
        print(f"Using existing directory: {os.path.abspath(download_dir)}")

    print(f"Found {len(links)} links. Starting download...")

    # Generate filename template based on user's choices
    filename_template = get_filename_template(args)

    # Show user what filename format will be used
    template_name = "custom"
    if not args.get('custom_template'):
        if args.get('no_date'):
            template_name = "no-date"
        elif args.get('title_only'):
            template_name = "title-only"
        elif args.get('creator_id'):
            template_name = "creator-id"
        elif args.get('filename_preset'):
            template_name = args['filename_preset']
        else:
            template_name = "default"

    print(f"Using filename format: {template_name}")

    download_with_ytdlp(links, download_dir, use_cookies=use_cookies, use_watermark=use_watermark, filename_template=filename_template)

    # At the end of execution, print where metadata was saved
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    print(f"Downloaded video information saved to {current_time}_download_log.csv")

if __name__ == "__main__":
    main()
