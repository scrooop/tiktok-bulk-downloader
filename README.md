# TikTok Bulk Downloader

With the TikTok ban in about a week, I wanted to download all of the videos in my Favorites list, but realized there isn’t a reliable way to do that, so I threw this together – the first thing I’ve put on GitHub. I hope it's useful. You do need to follow the instructions here to get it to work, but it's fairly straightforward. If anything is unclear please let me know and I will answer your questions and improve the script/this page.

This Python script enables users to download multiple TikTok videos efficiently using a user-generated list of video URLs (e.g., all of your Favorites, all of your Liked, all videos posted by a specific user, etc.). With a the TikTok ban approaching, this tool provides an easy way to save large amounts of videos with a single click.

## Table of Contents
1. [About the Project](#about-the-project)
2. [Why This Project is Useful](#why-this-project-is-useful)
3. [Getting Started](#getting-started)
   * [Prerequisites](#prerequisites)
   * [Usage Instructions](#usage-instructions)
4. [Features](#features)
5. [Help and Support](#help-and-support)
6. [Maintainers](#maintainers)
7. [License](#license)

---

## About the Project

This script simplifies the process of downloading multiple TikTok videos. Whether you’re backing up your favorite TikToks, saving content for offline use, or preparing for the death of TikTok in about one week, this tool makes it quick and seamless.

### Key Highlights
- Batch downloads from a list of URLs.
- Metadata extraction for each video.
- Cookie support for authenticated downloads (e.g., private or restricted videos).
- Customizable output directories.

---

## Why This Project is Useful

TikTok lacks an official way to bulk download videos, especially private or restricted ones. This project bridges that gap by:
- Saving time with batch processing.
- Enabling private or restricted downloads using cookies.
- Providing detailed metadata logs for easier file management.

---

## Getting Started

### Prerequisites

1. **Install Python 3.6+**
   - Check if Python is installed:
     ```bash
     python3 --version
     ```
   - Download Python from [python.org](https://www.python.org/) if needed.

2. **Install yt-dlp**
   - The script relies on [yt-dlp](https://github.com/yt-dlp/yt-dlp). Install it via pip:
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

## Features

- **Batch Processing**: Quickly download multiple videos from a URL list.
- **Metadata Logging**: Extract and save details like upload date, uploader, title, duration, and resolution.
- **Cookie Support**: Access private/restricted videos with session cookies.
- **Custom Directory**: Save videos in any specified folder.

---

## Help and Support

For assistance:
- [Open an issue on GitHub](https://github.com/scrooop/tiktok-bulk-downloader/issues).
- Review the [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#usage) for advanced options.

---

## Maintainers

This project is maintained by **[scrooop](https://github.com/scrooop)**. Contributions are welcome! Feel free to fork the repository and submit pull requests.

---

## License

This project is licensed under the MIT License. For more details, see the [LICENSE](LICENSE) file.

---

Feel free to reach out if you encounter issues or have suggestions for improvement.
