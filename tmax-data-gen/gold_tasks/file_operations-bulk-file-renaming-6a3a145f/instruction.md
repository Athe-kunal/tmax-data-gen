As a release archivist packaging deliverables, I need to prepare a set of files for distribution. The files are located in the `/home/user/deliverables` directory and are a mix of Python scripts, data files, and documentation. The files have inconsistent naming conventions, which makes it difficult to manage and distribute them.

My goal is to bulk rename the files in the `/home/user/deliverables` directory to have a more consistent naming convention. The new naming convention should include a prefix that indicates the type of file (e.g., `script_`, `data_`, `doc_`), followed by a unique identifier. The unique identifier should be a zero-padded, three-digit number, starting from 001.

For example, if the directory contains the following files:
`file1.py`, `file2.txt`, `file3.md`, etc.
I want to rename them to:
`script_001.py`, `data_001.txt`, `doc_001.md`, etc.

However, I also want to preserve the original file permissions and timestamps. I do not want to modify the contents of the files in any way.

To verify that the renaming process was successful, I want to generate a log file that contains the names of the original files and their corresponding new names. The log file should be named `rename_log.txt` and should be located in the `/home/user` directory.

The format of the log file should be:
`original_name -> new_name`
For example:
`file1.py -> script_001.py`
`file2.txt -> data_001.txt`
`file3.md -> doc_001.md`

Please assist me in bulk renaming these files and generating the log file. You can use any terminal commands or write short shell scripts to accomplish this task.
