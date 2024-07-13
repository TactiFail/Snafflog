# What?

Snafflog.

# What???

It parses [Snaffler](https://github.com/SnaffCon/Snaffler) logs into a Sqlite3 DB in case you didn't RTFM and pass in `-t json`, like a fucking dingus.

# Why?

Because I was a fucking dingus and didn't RTFM and I had a 59.7 MB log file to dig though.

# Oh.

Yeah.

# Usage?

No.

# Please?

`./snafflog.py <log_file_path> <db_file_path>` and it will create the Sqlite3 DB file for you. If one exists when you run this, it will append log files and you will end up with duplicates. So don't do that.

# I got a `[!]` line  :(

:(

# :(

Yeah that can happen sometimes. The `FILE_REGEX` string can be touchy, though `SHARE_REGEX` and `INFO_REGEX` are usually fine. Pop the offending regex and line(s) into [a regex debugger](https://regex101.com) and fix it. Don't open an Issue because I have already spent so long getting it to work on all of my files that you can share at least some that pain yourself.

Feel free to PR an update if you do though.