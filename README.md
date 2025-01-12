# TikTok Bulk Downloader

With the TikTok ban in about a week, I wanted to download all of the videos in my Favorites list, but realized there isn’t a reliable way to do that, so I threw this together. You do need to follow the instructions here before running the script, but it's fairly straightforward. If anything is unclear please let me know and I will answer your questions and improve the script/this page.

This Python script enables users to batch download TikTok videos efficiently using a user-generated list of video URLs (e.g., all of your Favorites, all of your Liked, all videos posted by a specific user, etc.) at once.

---

## Getting Started

### Prerequisites

1. **Install Python 3.6+**
   - Check if Python is installed. Open Terminal and type:
     ```bash
     python3 --version
     ```
   - Download Python from [python.org](https://www.python.org/) if needed.

2. **Install yt-dlp**
   - The script relies on [yt-dlp](https://github.com/yt-dlp/yt-dlp). In the terminal type:
     ```bash
     pip install yt-dlp
     ```

3. **(Optional) Export TikTok Cookies**
   - Export your TikTok session cookies for downloading private or restricted videos. Save them as `cookies.txt` in the same directory as this script.

---

### Usage Instructions

1. **Prepare Your URL List**
   - Log in to TikTok via your browser.
   - Navigate to the desired video page (e.g., your Favorites).
   - Scroll to the bottom of the page to load all videos.
   - Open developer tools, click **Console**, and run:
     ```javascript
     const videoLinks = [...document.querySelectorAll('a[href*="/video/"]')].map(a => a.href);
     console.log(`Total video links found: ${videoLinks.length}`);
     copy(videoLinks.join('\n'));
     ```
   - Paste the links into a text file and name it `links.txt`. Save it in the script’s directory.

2. **Run the Script**
   - Open a terminal in the script’s directory.
   - Execute the script with the following command:
     ```bash
     python3 tiktokBulkDownloader.py [--cookies] [--links <filename>]
     ```
   - Optional Flags:
     - `--cookies`: Use this if you have saved a `cookies.txt` file for private or restricted videos.
     - `--links <filename>`: Specify a custom file containing TikTok video URLs (default is `links.txt`).

3. **Specify Download Directory**
   - The script will prompt you to enter a directory for saving videos. If it doesn’t exist, it will be created.

4. **Check Logs**
   - A log file will be generated in the format `YYYY-MM-DD_HH-MM_download_log.csv`, containing metadata for downloaded videos.

---

## Help and Support

For assistance:
- [Open an issue on GitHub](https://github.com/scrooop/tiktok-bulk-downloader/issues).
- Review the [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#usage) for advanced options.

Feel free to reach out if you encounter issues or have suggestions for improvement.
