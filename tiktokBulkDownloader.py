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

# Global variable to prevent multiple retries
retry_attempted = False

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

            # Define yt-dlp output template with byte-based truncation
            output_template = os.path.join(
                download_dir,
                "%(upload_date).10s - %(uploader).50s - %(title).180B.%(ext)s"
            )

            # yt-dlp command for downloading the video
            cmd_download = [
                "yt-dlp",
                "--progress",
                "--no-warnings",
                "-o", output_template
            ]
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
        download_with_ytdlp(failed_links, download_dir, use_cookies=use_cookies, use_watermark=use_watermark)
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

    print(f"Found {len(links)} links. Starting download...")
    download_with_ytdlp(links, download_dir, use_cookies=use_cookies, use_watermark=use_watermark)

    # At the end of execution, print where metadata was saved
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    print(f"Downloaded video information saved to {current_time}_download_log.csv")

if __name__ == "__main__":
    main()
