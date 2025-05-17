import csv
import os
from collections import defaultdict

INPUT_FILE = 'actions.csv'
OUTPUT_FILE = 'paths_summary.csv'
TARGET_ACTION = 'A'

USER_DATA_DIR = 'user_data'
USER_PATHS_DIR = 'user_paths'


def ensure_dirs():
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    os.makedirs(USER_PATHS_DIR, exist_ok=True)


def split_csv_by_user(input_file):
    print("Splitting input CSV into per-user files...")

    open_files = {}
    writers = {}

    with open(input_file, newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            user = row['User']
            user_file = os.path.join(USER_DATA_DIR, f'{user}.csv')
            if user not in open_files:
                uf = open(user_file, 'w', newline='')
                open_files[user] = uf
                writer = csv.DictWriter(uf, fieldnames=reader.fieldnames, delimiter=';')
                writer.writeheader()
                writers[user] = writer
            writers[user].writerow(row)

    for f in open_files.values():
        f.close()

    print("Split complete.")


def sort_user_file_and_extract_paths():
    print("Processing per-user files to extract paths...")
    for user_file in os.listdir(USER_DATA_DIR):
        user_path = os.path.join(USER_DATA_DIR, user_file)

        # Read and sort rows by Date as string descending
        with open(user_path, newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = sorted(reader, key=lambda r: r['Date'], reverse=True)

        user = user_file.replace('.csv', '')
        output_path_file = os.path.join(USER_PATHS_DIR, f'{user}_paths.csv')

        with open(output_path_file, 'w', newline='') as out_f:
            writer = csv.writer(out_f)
            i = 0
            while i < len(rows):
                if rows[i]['Action'] == TARGET_ACTION:
                    path = [TARGET_ACTION]
                    i += 1
                    while i < len(rows) and rows[i]['Action'] != TARGET_ACTION:
                        path.append(rows[i]['Action'])
                        i += 1
                    if len(path) > 1:
                        writer.writerow([' -> '.join(path)])
                else:
                    i += 1


def aggregate_paths():
    print("Aggregating paths across users...")
    path_counts = defaultdict(int)
    path_users = defaultdict(set)

    for path_file in os.listdir(USER_PATHS_DIR):
        user = path_file.split('_')[0]
        full_path = os.path.join(USER_PATHS_DIR, path_file)
        with open(full_path, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    path = row[0]
                    path_counts[path] += 1
                    path_users[path].add(user)

    with open(OUTPUT_FILE, 'w', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['Path', 'Occurrences', 'Users'])
        for path, count in path_counts.items():
            writer.writerow([path, count, len(path_users[path])])

    print(f"Created summary: {OUTPUT_FILE}")


def main():
    ensure_dirs()
    split_csv_by_user(INPUT_FILE)
    sort_user_file_and_extract_paths()
    aggregate_paths()


if __name__ == '__main__':
    main()
