# TikTok Bulk Downloader

With the TikTok ban in about a week, I wanted to download all of the videos in my Favorites list, but realized there isn’t a reliable way to do that, so I threw this together. You do need to follow the instructions here before running the script, but it's fairly straightforward. If anything is unclear please let me know and I will answer your questions and improve the script/this page.

This Python script enables users to batch download TikTok videos efficiently using a user-generated list of video URLs (e.g., all of your Favorites, all of your Liked, all videos posted by a specific user, etc.) at once.

![Script Running Example](images/screenshot)

---

## Getting Started

### Prerequisites

1. Save tiktokBulkDownloader.py to a new directory.

2. **Install yt-dlp**
   - The script relies on [yt-dlp](https://github.com/yt-dlp/yt-dlp). If you don't have it, in the terminal type:
     ```bash
     pip install yt-dlp
     ```

3. **(Optional) Export TikTok Cookies**
   - Export your TikTok session cookies for downloading private or restricted videos. Save them as `cookies.txt` in the same directory as this script.

---

### Usage Instructions

1. **Prepare Your URL List**
   
   #### Method 1: Using TikTok's "Download Your Data" Tool
   - Go to [TikTok's "Download Your Data" page](https://www.tiktok.com/setting/download-your-data) and request your data in **TXT format**.
   - Wait for TikTok to generate the data file, then download it once it's ready.
   - Locate the specific file that contains the video links, such as `Favorite Videos.txt` for favorited videos or `Like List.txt` for liked videos.
   - Use the `--links` argument to specify this file when running the script:
     ```bash
     python3 tiktokBulkDownloader.py --links <filename>
     ```
   - The script will automatically process the file, extracting the links and creating a pure list of video URLs before proceeding with the download.

   #### Method 2: Manually Choose Any Page from Which to Download All Videos
   - Log in to TikTok via your browser.
   - Navigate to the desired video page (e.g., Profile > Favorites, Profile > Liked, Creator's Profile page, etc.).
   - Scroll to the bottom of the page to load all videos.
   - Open developer tools, click **Console**, and run:
     ```javascript
     const videoLinks = [...document.querySelectorAll('a[href*="/video/"]')].map(a => a.href);
     console.log(`Total video links found: ${videoLinks.length}`);
     copy(videoLinks.join('\n'));
     ```
   - Paste the links into a text file and name it `links.txt`. Save it in the script’s directory.

2. **Run the Script**
   - Open Terminal and navigate to the directory containing the script.
   - Execute the script with the following command:
     ```bash
     python3 tiktokBulkDownloader.py [--cookies] [--links <filename>] [--watermark]
     ```
   - Optional Flags:
     - `--cookies`: Use this if you have saved a `cookies.txt` file for private or restricted videos.
     - `--links <filename>`: Specify a custom file containing TikTok video URLs (default is `links.txt`).
     - `--watermark`: Use this if you want the TikTok watermark on your videos. I've noticed that the download speed may be slower if you use this option, and some videos that otherwise download successfully may fail.

3. **Specify Download Directory**
   - The script will prompt you to enter a directory for saving videos. If it doesn’t exist, it will be created.

4. **File Naming Format**
   - Videos are saved with a descriptive filename (upload date, creator, title) with the following format:
     ```
     YYYY-MM-DD - creator username - video title.mp4
     ```
   - Invalid characters in the title or username are replaced with underscores (`_`) to ensure compatibility.

5. **Check Logs**
   - A log file will be generated in the format YYYY-MM-DD_HH-MM_download_log.csv, containing metadata for all successfully downloaded videos, including details such as upload date, uploader, title, duration, and resolution.
   - In the event of any failed downloads, a separate log file will be created in the format YYYY-MM-DD_HH-MM_failed_downloads_log.txt, documenting the failed video links along with detailed error messages for troubleshooting.

---

## Help and Support

For assistance:
- [Open an issue on GitHub](https://github.com/scrooop/tiktok-bulk-downloader/issues).
- Review the [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#usage) for advanced options.

Feel free to reach out if you encounter issues or have suggestions for improvement.
