import csv
import os
import sys
import argparse
from collections import defaultdict

# Increase CSV field size limit to maximum allowed by the system
csv.field_size_limit(sys.maxsize)

OUTPUT_FILE = 'paths_summary.csv'
DETAILED_OUTPUT_FILE = 'paths_detailed.csv'
PLANTUML_FILE = 'paths_diagram.puml'
TARGET_ACTION = 'A'

USER_DATA_DIR = 'user_data'
USER_PATHS_DIR = 'user_paths'


def ensure_dirs(output_dir):
    os.makedirs(output_dir + "/" + USER_DATA_DIR, exist_ok=True)
    os.makedirs(output_dir + "/" + USER_PATHS_DIR, exist_ok=True)


def split_csv_by_user(input_file, output_dir):
    if os.listdir(output_dir + "/" + USER_DATA_DIR):
        print("User data directory already exists and is not empty. Skipping split.")
        return

    print("Splitting input CSV into per-user files...")

    with open(input_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            user = row['User']
            user_file = os.path.join(output_dir + "/" + USER_DATA_DIR, f'{user}.csv')

            file_exists = os.path.exists(user_file)
            with open(user_file, 'a', newline='', encoding='utf-8') as uf:
                writer = csv.DictWriter(uf, fieldnames=reader.fieldnames, delimiter=';')
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)

    print("Split complete.")


def sort_user_file_and_extract_paths(output_dir):
    if os.listdir(output_dir + "/" + USER_PATHS_DIR):
        print("User paths directory already exists and is not empty. Skipping path extraction.")
        return

    print("Processing per-user files to extract paths...")
    for user_file in os.listdir(output_dir + "/" + USER_DATA_DIR):
        user_path = os.path.join(output_dir + "/" + USER_DATA_DIR, user_file)

        with open(user_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = sorted(reader, key=lambda r: r['Date'], reverse=True)

        user = user_file.replace('.csv', '')
        output_path_file = os.path.join(output_dir + "/" + USER_PATHS_DIR, f'{user}_paths.csv')

        with open(output_path_file, 'w', newline='', encoding='utf-8') as out_f:
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


def aggregate_paths(output_dir):
    print("Aggregating paths across users...")
    path_counts = defaultdict(int)
    path_users = defaultdict(set)
    action_stats = defaultdict(lambda: {'occurrences': 0, 'users': set()})

    # First pass: collect path statistics
    for path_file in os.listdir(output_dir + "/" + USER_PATHS_DIR):
        user = path_file.split('_')[0]
        full_path = os.path.join(output_dir + "/" + USER_PATHS_DIR, path_file)
        with open(full_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    path = row[0]
                    path_counts[path] += 1
                    path_users[path].add(user)

    # Second pass: collect action statistics by sequence position
    for path, users in path_users.items():
        actions = path.split(' -> ')
        for seq, action in enumerate(actions, start=1):
            key = (seq, action)
            action_stats[key]['occurrences'] += path_counts[path]
            action_stats[key]['users'].update(users)

    # Write summary of paths (unchanged)
    with open(output_dir + "/" + OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['Path', 'Occurrences', 'Users'])
        for path, count in path_counts.items():
            writer.writerow([path, count, len(path_users[path])])

    print(f"Created summary: {OUTPUT_FILE}")

    # Write detailed action breakdown in the new format
    with open(output_dir + "/" + DETAILED_OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_detail:
        writer = csv.writer(f_detail)
        writer.writerow(['Sequence', 'Action', 'Occurrences', 'Users'])
        
        # Sort by sequence number first, then by action
        for (seq, action), stats in sorted(action_stats.items(), key=lambda x: (x[0][0], x[0][1])):
            writer.writerow([
                seq,
                action,
                stats['occurrences'],
                len(stats['users'])
            ])

    print(f"Created detailed action breakdown: {DETAILED_OUTPUT_FILE}")


def generate_plantuml_diagram(  output_dir):
    print("Generating PlantUML class diagram...")
    actions = set()
    connections = set()

    with open(output_dir + "/" + OUTPUT_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            path = row['Path']
            steps = path.split(' -> ')
            actions.update(steps)
            for i in range(len(steps) - 1):
                connections.add((steps[i], steps[i + 1]))

    with open(output_dir + "/" + PLANTUML_FILE, 'w', encoding='utf-8') as f:
        f.write('@startuml\n\n')
        for action in actions:
            f.write(f'class {action} {{}}\n')
        f.write('\n')
        for a1, a2 in connections:
            f.write(f'{a1} --> {a2}\n')
        f.write('\n@enduml\n')

    print(f"Created PlantUML diagram: {PLANTUML_FILE}")


def main(input_file, output_dir):
    ensure_dirs(output_dir)
    split_csv_by_user(input_file, output_dir)
    sort_user_file_and_extract_paths(output_dir)
    aggregate_paths(output_dir)
    generate_plantuml_diagram(output_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process actions CSV and generate paths.")
    parser.add_argument('--input', type=str, default='actions.csv', help="Input CSV filename")
    parser.add_argument('--output', type=str, default='output', help="Output directory")
    args = parser.parse_args()
    
    INPUT_FILE = args.input
    OUTPUT_DIR = args.output
    
    main(INPUT_FILE, OUTPUT_DIR)
