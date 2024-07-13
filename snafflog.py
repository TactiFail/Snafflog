#!/usr/bin/env python3

import regex
import sqlite3
import sys

# SQL INSERT batch size
BATCH_SIZE = 100

# Log entry regex patterns
# The Share one has been stable, but you may need to adjust FILE_REGEX if you are seeing weird directory or file names
FILE_REGEX =  r"^\[(?<domain>[A-z.]+)\\(?<username>[A-z.]+)@(?<server>[A-Za-z0-9]+(-[A-Za-z0-9]+)+)\] (?<foundAtDate>\d{4}-\d{2}-\d{2}) (?<foundAtTime>\d{2}:\d{2}:\d{2})Z \[(?<type>\w+)\] \{(?<severity>\w+)\}\<(?<matchedRule>\w+)\|(?<permissions>\w+)\|(?<regex>.*?)\|(?<size>\d+(\.\d+)?[kKmMgG]?B?)\|(?<modifiedDate>\d{4}-\d{2}-\d{2}) (?<modifiedTime>\d{2}:\d{2}:\d{2})Z\>\(\\\\(?P<target>[0-9.]+)\\(?P<share>[\w\.\- \$\-\&]+)\\(?P<path>.+\\)?(?P<filename>[^\\]+)\) ?(?P<context>.+)?$"
SHARE_REGEX = r"^\[(?<domain>[A-z.]+)\\(?<username>[A-z.]+)@(?<server>[A-Za-z0-9]+(-[A-Za-z0-9]+)+)\] (?<foundAtDate>\d{4}-\d{2}-\d{2}) (?<foundAtTime>\d{2}:\d{2}:\d{2})Z \[(?<type>\w+)\] \{(?<severity>\w+)\}\<\\\\(?<target>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\\(?P<share>[\w\.\- \$\-\&]+)\>\((?<permissions>[A-Z]*)\) ?(?<description>.*)?$"
INFO_REGEX =  r"^\[(?<domain>[A-z.]+)\\(?<username>[A-z.]+)@(?<server>[A-Za-z0-9]+(-[A-Za-z0-9]+)+)\] (?<foundAtDate>\d{4}-\d{2}-\d{2}) (?<foundAtTime>\d{2}:\d{2}:\d{2})Z \[Info\].*$"

def create_tables(conn):
    with conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            domain TEXT,
            username TEXT,
            server TEXT,
            foundAtDate TEXT,
            foundAtTime TEXT,
            type TEXT,
            severity TEXT,
            matchedRule TEXT,
            permissions TEXT,
            regex TEXT,
            size TEXT,
            modifiedDate TEXT,
            modifiedTime TEXT,
            target TEXT,
            share TEXT,
            path TEXT,
            filename TEXT,
            context TEXT
        )
        ''')

        conn.execute('''
        CREATE TABLE IF NOT EXISTS shares (
            domain TEXT,
            username TEXT,
            server TEXT,
            foundAtDate TEXT,
            foundAtTime TEXT,
            type TEXT,
            severity TEXT,
            target TEXT,
            share TEXT,
            permissions TEXT,
            description TEXT
        )
        ''')


def insert_file_data(conn, files_data):
    with conn:
        conn.executemany('''
        INSERT INTO files (
            domain, username, server, foundAtDate, foundAtTime, type, severity,
            matchedRule, permissions, regex, size, modifiedDate, modifiedTime,
            target, share, path, filename, context
        ) VALUES (
            :domain, :username, :server, :foundAtDate, :foundAtTime, :type, :severity,
            :matchedRule, :permissions, :regex, :size, :modifiedDate, :modifiedTime,
            :target, :share, :path, :filename, :context
        )
        ''', files_data)


def insert_share_data(conn, shares_data):
    with conn:
        conn.executemany('''
        INSERT INTO shares (
            domain, username, server, foundAtDate, foundAtTime, type, severity,
            target, share, permissions, description
        ) VALUES (
            :domain, :username, :server, :foundAtDate, :foundAtTime, :type, :severity,
            :target, :share, :permissions, :description
        )
        ''', shares_data)


def parse_logs(path, db_path):
    conn = sqlite3.connect(db_path)
    create_tables(conn)

    file_pattern = regex.compile(FILE_REGEX)
    share_pattern = regex.compile(SHARE_REGEX)
    info_pattern = regex.compile(INFO_REGEX)

    files_data = []
    shares_data = []

    with open(path) as log:
        print(f"Parsing {sum(1 for _ in log)} lines...")
        log.seek(0)
        for line in log:
            line = line.strip()
            file_match = file_pattern.match(line)
            share_match = share_pattern.match(line)
            info_match = info_pattern.match(line)
            if file_match:
                files_data.append(file_match.groupdict())
            elif share_match:
                shares_data.append(share_match.groupdict())
            elif info_match:
                continue
            elif len(line) > 64: # 64 should be enough for any of the regular status update messages
                print(f"[!] {line}")

            if len(files_data) >= BATCH_SIZE:
                insert_file_data(conn, files_data)
                files_data.clear()

            if len(shares_data) >= BATCH_SIZE:
                insert_share_data(conn, shares_data)
                shares_data.clear()

        # Insert any remaining data after batching
        if files_data:
            insert_file_data(conn, files_data)
        if shares_data:
            insert_share_data(conn, shares_data)

    print(f"{conn.execute('SELECT COUNT(*) FROM files').fetchone()[0]} files and {conn.execute('SELECT COUNT(*) FROM shares').fetchone()[0]} shares recorded")
    conn.close()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: ./snafflog.py <log_file_path> <db_file_path>")
    else:
        parse_logs(sys.argv[1], sys.argv[2])