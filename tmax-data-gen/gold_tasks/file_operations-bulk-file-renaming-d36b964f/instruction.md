As a backup administrator, I am tasked with archiving data for our company. I have a directory located at `/home/user/archived_data` that contains a large number of files with inconsistent naming conventions. The files are a mix of documents, images, and videos, and they all have a `.data` extension. My goal is to bulk rename these files to have a more consistent naming convention.

The current naming convention is a mix of letters and numbers, but it does not provide any meaningful information about the contents of the files. I want to rename the files to include a prefix that indicates the type of file (e.g., `doc_`, `img_`, `vid_`), followed by a unique identifier. The unique identifier should be a zero-padded, three-digit number, starting from 001.

For example, if the directory contains the following files:
`file1.data`, `file2.data`, `file3.data`, etc.
I want to rename them to:
`doc_001.data`, `doc_002.data`, `doc_003.data`, etc.

However, I also want to preserve the original file permissions and timestamps. I do not want to modify the contents of the files in any way.

To verify that the renaming process was successful, I want to generate a log file that contains the names of the original files and their corresponding new names. The log file should be named `rename_log.txt` and should be located in the `/home/user` directory.

The format of the log file should be:
`original_name -> new_name`
For example:
`file1.data -> doc_001.data`
`file2.data -> doc_002.data`
`file3.data -> doc_003.data`

Please assist me in bulk renaming these files and generating the log file.
