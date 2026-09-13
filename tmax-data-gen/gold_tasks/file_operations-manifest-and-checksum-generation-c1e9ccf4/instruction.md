As a backup administrator archiving data, I need to create a backup of my important files and generate a manifest with checksums for verification. I have a directory `/home/user/data/` containing various files, including documents, images, and videos. The directory has the following structure:
- `/home/user/data/documents/` contains text documents (`*.txt`).
- `/home/user/data/images/` contains image files (`*.jpg`, `*.png`).
- `/home/user/data/videos/` contains video files (`*.mp4`).

My goal is to create a backup directory `/home/user/backup/` with the same structure as the original directory, and generate a SHA-256 checksum manifest of all files in the backup directory.

To achieve this, I need to:
1. Create the backup directory structure.
2. Copy all files from `/home/user/data/` to `/home/user/backup/`, preserving the directory structure.
3. Generate a SHA-256 checksum manifest of all files in the backup directory.

The manifest file should have the following format:
`<sha256sum>  <relative_path_from_backup_dir>`, for example: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  documents/example.txt`.

The manifest entries should be sorted alphabetically by the relative file path.

Please create the necessary files and directories, and generate the manifest file. After completing the task, create a log file `/home/user/backup/log.txt` with the message "Backup created successfully."

Note: The backup directory should be created in the `/home/user/` directory, and the manifest file should be named `manifest.sha256` and located in the `/home/user/backup/` directory.
