# TikTok Videos Bulk Downloader

#### TO DO:
# prepend each video with creator's username

'''
This script allows you to bulk download TikTok videos from a list of URLs.
It leverages the yt-dlp tool for video extraction and supports using cookies
for authenticated downloads of restricted or private videos.

Usage:

Before running the script:

1. Open your browser and log in to TikTok.
2. Go to the page from which you want to download all videos. For example, if you want to download all of your Favorited videos,
    navigate to your profile page, then click Favorites.
3. Scroll all the way to the bottom of the page to load all of the videos on that page.
4. Open developer tools (right-click > Inspect) and click Console.
5. Run the following command in the console to copy all video links to your clipboard:

const videoLinks = [...document.querySelectorAll('a[href*="/video/"]')].map(a => a.href);
console.log(`Total video links found: ${videoLinks.length}`);
console.log(videoLinks);
copy(videoLinks.join('\n'));

6. Paste the links into a text file and save it as links.txt in the same directory as this script (should contain one TikTok video URL per line).
7. (Optional) Export your TikTok session cookies to a file named "cookies.txt"
  if you need to download private or restricted videos.
8. Run the script via:

     python3 tiktokFavLinksDownload.py

      Optional Flags:

    --cookies: Use this if you have saved a cookies.txt file for private or restricted videos.
    --links <filename>: Specify a custom file containing TikTok video URLs (default is links.txt).
    --watermark: Use this if you want the TikTok watermark on your videos. I've noticed that the download speed may be slower if you use this option,
    and some videos that otherwise download successfully may fail.

The script prompts for a download directory, saves each video there,
and logs failed downloads along with errors in a timestamped log file.

'''

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

def download_with_ytdlp(links, download_dir, use_cookies=False, use_watermark=False):
    """
    Bulk-downloads a list of TikTok videos using yt-dlp and logs metadata.

    :param links: List of TikTok video URLs to download
    :type links: list[str]
    :param download_dir: Target directory to save the downloaded videos
    :type download_dir: str
    :param use_cookies: Whether to append --cookies cookies.txt to yt-dlp
                        commands for authenticated requests
    :type use_cookies: bool
    :param use_watermark: Whether to use the "download" format (watermarked videos)
    :type use_watermark: bool
    :return: None
    """
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

    # Basic constraints for filename length
    max_path_length = 255
    ext = ".mp4"

    # Track success/failure statistics
    total_links = len(links)
    successful_downloads = 0
    failed_downloads = 0
    failed_links = []  # Collect links that fail for retry

    # Iterate through each link
    for index, link in enumerate(links, start=1):
        try:
            # Print exactly one blank line before the [index/total] line
            print()
            print(f"[{index}/{total_links}]: {link}")

            # Step 1: Fetch JSON metadata (including upload date, uploader, title)
            cmd_metadata = ["yt-dlp", "--dump-json"]
            if use_cookies:
                cmd_metadata += ["--cookies", "cookies.txt"]
            cmd_metadata.append(link)

            # Capture JSON metadata from yt-dlp
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

            # Construct metadata dictionary
            metadata = {
                "upload_date": formatted_date,
                "uploader": data.get("uploader", "unknown_uploader"),
                "title": data.get("title", "Untitled"),
                "url": link,
                "duration": data.get("duration", ""),
                "view_count": data.get("view_count", ""),
                "like_count": data.get("like_count", ""),
                "comment_count": data.get("comment_count", ""),
                "repost_count": data.get("repost_count", ""),
                "resolution": f"{data.get('height', '')}p" if data.get("height") else "",
            }

            # Sanitize filename components
            upload_date_sanit = re.sub(r'[<>:"/\\|?*]', '_', metadata["upload_date"])
            uploader_sanit = re.sub(r'[<>:"/\\|?*]', '_', metadata["uploader"])
            title_sanit = re.sub(r'[<>:"/\\|?*]', '_', metadata["title"])
            combined_filename = f"{upload_date_sanit} - {uploader_sanit} - {title_sanit}"

            # Enforce OS constraints
            available_length = max_path_length - len(os.path.abspath(download_dir)) - len(ext) - 1
            if len(combined_filename) > available_length:
                print(f"\n[INFO] Filename truncated: '{combined_filename}' -> '{combined_filename[:available_length]}'")
                combined_filename = combined_filename[:available_length]

            # Final output path with ".mp4"
            output_path = os.path.join(download_dir, f"{combined_filename}{ext}")

            # Step 2: Download the video with the newly formatted filename
            cmd_download = [
                "yt-dlp",
                "--progress",
                "--no-warnings",
                "-o", output_path,
            ]
            if use_watermark:
                cmd_download += ["--format", "download"]
            if use_cookies:
                cmd_download += ["--cookies", "cookies.txt"]
            cmd_download.append(link)

            # Print a blank line before the progress bar
            print()
            subprocess.run(cmd_download, check=True)

            # Append metadata to the global list for logging
            downloaded_metadata.append([
                metadata["upload_date"],
                metadata["uploader"],
                metadata["title"],
                metadata["url"],
                combined_filename,
                metadata["duration"],
                metadata["view_count"],
                metadata["like_count"],
                metadata["comment_count"],
                metadata["repost_count"],
                metadata["resolution"],
            ])

            print(" SUCCESS")
            successful_downloads += 1

        except Exception as e:
            print(" FAILED")
            failed_downloads += 1
            failed_links.append(link)  # Collect the failed link

            # Log the error details to the timestamped log file
            with open(failed_log_file, "a", encoding="utf-8") as f:
                sanitized_link = link.strip() if link else "(Invalid or missing link)"
                error_message = str(e).strip()
                f.write(f"[{index}/{total_links}]\n")
                if '\n' in error_message:
                    error_lines = error_message.split('\n', 1)
                    f.write(f"Error: {error_lines[0]}\n{error_lines[1]}\n")
                else:
                    f.write(f"Error: {error_message}\n")
                f.write("-" * 40 + "\n")

    # Retry logic for failed links
    if failed_links:
        print(f"\nRe-attempting download for {len(failed_links)} failed links...\n")
        download_with_ytdlp(failed_links, download_dir, use_cookies=use_cookies, use_watermark=use_watermark)

    # Save metadata one final time after retries
    save_metadata_to_csv()

    # Final summary
    print("\nDownload process complete.")
    print(f"Successful downloads: {successful_downloads}/{total_links}")
    print(f"Failed downloads: {failed_downloads}/{total_links}")
    if failed_downloads > 0 and not use_cookies:
        print("Retrying with cookies (using '--cookies') may allow successful downloads for the failed links.")


def main():
    """
    Main entry point: reads user input, checks for cookies usage,
    validates arguments, loads input file (default or specified with --links),
    and calls the download function.
    """
    # Register signal handler for Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)

    # Recognized arguments
    valid_args = {"--cookies", "--links", "--watermark"}
    provided_args = set(arg for arg in sys.argv[1:] if arg.startswith("-"))
    invalid_args = provided_args - valid_args

    # Check for invalid arguments
    if invalid_args:
        print(f"Error: Unrecognized argument(s): {', '.join(invalid_args)}")
        print("Usage: python tiktokBulkDownloader.py [--cookies] [--links <filename>] [--watermark]")
        return

    # Check for cookies and custom links file arguments
    use_cookies = "--cookies" in sys.argv
    use_watermark = "--watermark" in sys.argv
    links_arg_index = sys.argv.index("--links") + 1 if "--links" in sys.argv else None

    # Validate links file argument if provided
    input_file = sys.argv[links_arg_index] if links_arg_index else "links.txt"
    if links_arg_index and (
        links_arg_index >= len(sys.argv) or sys.argv[links_arg_index].startswith("-")
    ):
        print("Error: Missing filename after '--links'.")
        print("Usage: python tiktokBulkDownloader.py [--cookies] [--links <filename>] [--watermark]")
        return

    # Prompt for directory to store downloads
    download_dir = input("Enter the name of the directory to save the videos: ").strip()
    if not download_dir:
        print("No directory name provided. Exiting.")
        return

    # Attempt to create the directory if it doesn't exist
    if not os.path.exists(download_dir):
        try:
            os.mkdir(download_dir)
            print(f"Created directory: {download_dir}")
        except Exception as e:
            print(f"Failed to create directory {download_dir}: {e}")
            return

    # Validate input file existence
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found. Please create it and add your video links.")
        return

    # Clean the input file to extract only valid links
    links = clean_links_file(input_file)

    if not links:
        print("No valid links found in the input file.")
        return

    print(f"Found {len(links)} links. Starting download...")
    download_with_ytdlp(links, download_dir, use_cookies=use_cookies, use_watermark=use_watermark)

    # At the end of execution, print where metadata was saved
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    print(f"Downloaded video information saved to {current_time}_download_log.csv")


if __name__ == "__main__":
    main()