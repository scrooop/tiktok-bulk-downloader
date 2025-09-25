> [!NOTE]
> **U.S. TikTok availability:** TikTok remains accessible while a divestiture law is pending enforcement. See **[Legal status & disclosures](#legal-status--disclosures)** for details. *(Updated 2025-09-25)*

# TikTok Bulk Downloader

In light of ongoing U.S. legal requirements that could restrict TikTok if divestiture isn't completed, this script helps users download their favorite TikTok videos. You do need to follow the instructions here before running the script, but it's fairly straightforward. If anything is unclear please let me know and I will answer your questions and improve the script/this page.

This Python script enables users to batch download videos you own or have permission to download using a user-generated list of video URLs (e.g., all of your Favorites, all of your Liked, all videos posted by a specific user, etc.) at once.

[![Donate](https://img.shields.io/badge/Donate-Cash%20App-lightgrey)](#donate)

## Getting Started

### Prerequisites

1. **Python 3.6 or later** is required (the script uses f-strings)
   - Check your version: `python3 --version`
   - If you need to install Python, visit [python.org](https://www.python.org/downloads/)

2. Save tiktokBulkDownloader.py to a new directory.

3. **Install yt-dlp**
   - The script relies on [yt-dlp](https://github.com/yt-dlp/yt-dlp). If you don't have it, in the terminal type:
     ```bash
     pip install yt-dlp
     ```

4. **(Optional) Export TikTok Cookies** for private/restricted videos

   To download private or restricted videos, you'll need to export your TikTok session cookies:

   **Chrome/Edge/Brave:**
   - Install [Get cookies.txt locally](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Log into TikTok, click the extension icon, select "Export As"
   - Save as `cookies.txt` in the script directory

   **Firefox:**
   - Install [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
   - Follow similar steps as above

   **Manual Export:**
   - Open browser Developer Tools (F12) → Application/Storage → Cookies
   - Copy cookie values and format them as Netscape cookies.txt format

   Then use the `--cookies` option when running the script **only for content you're authorized to access**. Never share cookies or tokens.

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

   #### Method 2: Manually Extract Video Links from Browser

   **Note:** TikTok frequently changes their page structure, so this method may need adjustments.

   - Log in to TikTok via your browser
   - Navigate to the desired video page (e.g., Profile > Favorites, Profile > Liked, Creator's Profile)
   - **Important:** Scroll slowly to the bottom to ensure all videos load
   - Open Developer Tools (F12), go to **Console**, and try this script:
     ```javascript
     // Try to find video links - TikTok's structure may vary
     const videoLinks = [...document.querySelectorAll('a[href*="/video/"]')].map(a => a.href);

     // Alternative if above doesn't work:
     // const videoLinks = [...document.querySelectorAll('[data-e2e*="video"]')].map(el => el.closest('a')?.href).filter(Boolean);

     console.log(`Total video links found: ${videoLinks.length}`);
     if (videoLinks.length === 0) {
       console.log("No links found - TikTok may have changed their structure");
     } else {
       copy(videoLinks.join('\n'));
       console.log("Links copied to clipboard!");
     }
     ```
   - If the script finds links, paste them into `links.txt`
   - If it doesn't work, you may need to manually copy video URLs or use Method 1

2. **Run the Script**

   Open Terminal and navigate to the directory containing the script, then choose one of these options:

   **Basic Usage (requires links.txt file):**
   ```bash
   python3 tiktokBulkDownloader.py
   ```
   This expects a `links.txt` file in the same directory with your video URLs.

   **Specify a different file:**
   ```bash
   python3 tiktokBulkDownloader.py --links "Favorite Videos.txt"
   ```

   **Download a single video:**
   ```bash
   python3 tiktokBulkDownloader.py --links "https://www.tiktok.com/@user/video/123"
   ```

   **Common Options (where permitted):**
   - `--cookies`: Use cookies.txt for private/restricted videos
   - `--links <file>`: Specify input file or single URL (default: `links.txt`)
   - `--watermark`: Download watermarked versions (lower quality)
   - `--filename-custom [variables]`: Build custom filename (e.g., `date creator videoID`)
   - `--help`: Show all available options
   - `--list-variables`: Show filename customization variables

3. **Specify Download Directory**

   The script will prompt you for where to save videos with these options:
   - **Press Enter**: Save videos in the current directory (where you ran the script)
   - **Folder name** (e.g., `my_videos`): Creates a new folder in the current directory
   - **Full path**: Save to a specific location anywhere on your system
     - **Mac/Linux**: `/Users/name/Downloads/tiktoks` or `~/Downloads/tiktoks`
     - **Windows**: `C:\Users\Name\Downloads\tiktoks` or `%USERPROFILE%\Downloads\tiktoks`

   The script will automatically create directories that don't exist, including any parent directories needed.

4. **File Naming Format**
   - Videos are saved with a descriptive filename (upload date, creator, title) with the following format:
     ```
     YYYY-MM-DD_creator_username_video_title.mp4
     ```
   - Invalid characters in the title or username are replaced with underscores (`_`) to ensure compatibility.

5. **Check Logs**
   - A log file will be generated in the format YYYY-MM-DD_HH-MM_download_log.csv, containing metadata for all successfully downloaded videos, including details such as upload date, uploader, title, duration, and resolution.
   - In the event of any failed downloads, a separate log file will be created in the format YYYY-MM-DD_HH-MM_failed_downloads_log.txt, documenting the failed video links along with detailed error messages for troubleshooting.

---

## Customizing Filename Format

The script now has user-friendly command line options for filename customization.

### Easy Filename Options

**Remove Date from Filenames:**
```bash
python3 tiktokBulkDownloader.py --no-date
# Creates: creator_title.mp4
```

**Title Only:**
```bash
python3 tiktokBulkDownloader.py --title-only
# Creates: title.mp4
```

**Creator + Video ID:**
```bash
python3 tiktokBulkDownloader.py --creator-id
# Creates: creator_7106594312292453675.mp4
```

### Build Your Own Format

```bash
# Include video ID in filename
python3 tiktokBulkDownloader.py --filename-custom date creator videoID
# Creates: 2024-12-07_username_7106594312292453675.mp4

# Shorter date format
python3 tiktokBulkDownloader.py --filename-custom shortdate title
# Creates: 241207_video_title.mp4

# Mix and match any variables
python3 tiktokBulkDownloader.py --filename-custom year month creator title videoID
# Creates: 2024_12_username_video_title_7106594312292453675.mp4

# See all available variables:
python3 tiktokBulkDownloader.py --list-variables
```

**Available variables:**

**Basic Info:**
- `title` → Video title
- `creator` → Username/creator name
- `description` → Video description

**IDs:**
- `videoID` → TikTok video ID (e.g., 7106594312292453675)
- `creatorID` → Creator's user ID

**Dates:**
- `date` → Upload date (2024-12-07)
- `year` → Upload year (2024)
- `month` → Upload month (12)
- `day` → Upload day (07)
- `shortdate` → Short date format (241207)
- `fulldate` → Full date format (20241207)

**Statistics:**
- `views` → View count
- `likes` → Like count
- `comments` → Comment count
- `shares` → Share/repost count

**Video Properties:**
- `duration` → Video duration in seconds
- `resolution` → Video resolution
- `fps` → Frames per second
- `format` → Video format ID

**Other:**
- `platform` → Platform name (tiktok)
- `ext` → File extension (mp4)

### Advanced Options

**Use Presets:**
```bash
python3 tiktokBulkDownloader.py --filename-preset no-date
python3 tiktokBulkDownloader.py --filename-preset title-only
python3 tiktokBulkDownloader.py --filename-preset creator-id

# See all available presets:
python3 tiktokBulkDownloader.py --list-presets
```

**yt-dlp Templates (Advanced Users):**

For users familiar with yt-dlp, you can use native yt-dlp template syntax for maximum flexibility:

```bash
python3 tiktokBulkDownloader.py --filename-yt-dlp "%(uploader)s_%(upload_date)s.%(ext)s"
# Creates: creator_20220607.mp4

# Advanced example with conditional formatting
python3 tiktokBulkDownloader.py --filename-yt-dlp "%(upload_date>%Y%m%d)s_%(uploader).20s_%(title).100s.%(ext)s"
# Creates: 20220607_shortened_creator_shortened_title.mp4
```

This option provides full access to yt-dlp's template system including format specifiers, string manipulation, and conditional formatting. Review the [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#output-template) for complete template syntax reference.

### Preview Before Downloading

**Test filename formats without downloading:**
```bash
python3 tiktokBulkDownloader.py --preview-filename "https://tiktok.com/@user/video/123" --no-date
```

This shows exactly what the filename will look like and compares it with other available formats.

### Get Help

**See all options:**
```bash
python3 tiktokBulkDownloader.py --help
```

---

## Troubleshooting

### Common Error Messages and Solutions

**"Input file 'links.txt' not found"**
- Create a file named `links.txt` with your TikTok URLs (one per line)
- Or use `--links` to specify a different file

**"No formats available" or Download Fails**
- **Most likely cause**: TikTok is blocked in your location
- **Solution**: Use a VPN and connect to a server outside the US
- Try different VPN locations if one doesn't work

**"HTTP Error 403: Forbidden"**
- The video may be private or deleted
- Try using `--cookies` with your exported cookies

**yt-dlp Update Errors**
- Update yt-dlp: `pip install --upgrade yt-dlp`
- Or try: `pip3 install --upgrade yt-dlp`

**Permission Denied Errors (Mac/Linux)**
- Try: `pip install --user yt-dlp`
- Or use `sudo pip install yt-dlp` (not recommended)

**'python3' is not recognized (Windows)**
- Try using `python` instead of `python3`
- Or add Python to your PATH environment variable

### Understanding the Watermark Feature

**What `--watermark` actually does:**
- Downloads TikTok's "official download" version (the one you'd get from TikTok's download button)
- This version has **lower quality** (typically 576x1024 instead of 1080x1920)
- Contains embedded TikTok watermarks (username and TikTok logo)

**Without `--watermark` (default behavior):**
- Downloads the highest quality version available (typically 1080x1920)
- No TikTok watermarks or logos
- This is usually what you want

**When to use `--watermark`:**
- Only if you specifically need the "official" TikTok version
- Note: Download speeds may be slower and some videos may fail with this option

### Common Issues
- **"No formats available"**: Try using a VPN with different server locations
- **Private videos fail**: Use `--cookies` with exported browser cookies
- **Download speeds slow**: This is normal, especially with `--watermark` option
- **Some videos fail**: Check the failed downloads log file for specific error messages

### Checking Available Formats
To see what formats are available for a specific video:
```bash
yt-dlp -F "https://www.tiktok.com/@username/video/1234567890"
```

---

## Help and Support

For assistance:
- [Open an issue on GitHub](https://github.com/scrooop/tiktok-bulk-downloader/issues).

Feel free to reach out if you encounter issues or have suggestions for improvement.

---

## Donate
Scan to tip via Cash App:

[pending]

---

## Legal status & disclosures

### Current Status (U.S.)
- TikTok remains accessible in the U.S. as of Septemeber 2025.
- A divestiture/restructuring deal appears close; if finalized and approved, the app should remain available.
- If enforcement resumes without a completed deal, access and endpoints could change or break this tool.

### Legal & Intended Use
This tool is for downloading videos you own or have permission to download (e.g., your own posts, licensed/public‑domain content). Do not use it to infringe copyrights or to bypass DRM/technical protection measures (17 U.S.C. §1201). Follow TikTok's Terms and community policies at all times. The authors do not endorse or support any infringing use. Not legal advice.

### If TikTok Access Changes in the U.S.
If enforcement resumes or API/endpoint behavior changes, this tool may break or require updates (e.g., new extractors, changed cookies flow, or rate-limit adjustments). Please open an issue with reproducible logs.
