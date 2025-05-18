import csv
import os
import sys
import json
import argparse
from collections import defaultdict

# Increase CSV field size limit to maximum allowed by the system
csv.field_size_limit(sys.maxsize)

def load_config(config_path):
    """Load configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_dirs(output_dir, config):
    """Ensure required directories exist."""
    dirs = config['directories']
    os.makedirs(os.path.join(output_dir, dirs['user_data']), exist_ok=True)
    os.makedirs(os.path.join(output_dir, dirs['user_paths']), exist_ok=True)


def split_csv_by_user(input_file, output_dir, config):
    user_data_dir = os.path.join(output_dir, config['directories']['user_data'])
    if os.path.exists(user_data_dir) and os.listdir(user_data_dir):
        print("User data directory already exists and is not empty. Skipping split.")
        return

    print("Splitting input CSV into per-user files...")

    with open(input_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=config['csv']['delimiter'])
        for row in reader:
            user = row['User']
            user_file = os.path.join(user_data_dir, f'{user}.csv')

            file_exists = os.path.exists(user_file)
            with open(user_file, 'a', newline='', encoding='utf-8') as uf:
                writer = csv.DictWriter(uf, fieldnames=reader.fieldnames, 
                                      delimiter=config['csv']['delimiter'])
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)

    print("Split complete.")


def sort_user_file_and_extract_paths(output_dir, config):
    user_paths_dir = os.path.join(output_dir, config['directories']['user_paths'])
    user_data_dir = os.path.join(output_dir, config['directories']['user_data'])
    
    if os.path.exists(user_paths_dir) and os.listdir(user_paths_dir):
        print("User paths directory already exists and is not empty. Skipping path extraction.")
        return

    print("Processing per-user files to extract paths...")
    for user_file in os.listdir(user_data_dir):
        user_path = os.path.join(user_data_dir, user_file)

        with open(user_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=config['csv']['delimiter'])
            rows = sorted(reader, key=lambda r: r['Date'], reverse=True)

        user = user_file.replace('.csv', '')
        output_path_file = os.path.join(user_paths_dir, f'{user}_paths.csv')

        with open(output_path_file, 'w', newline='', encoding='utf-8') as out_f:
            writer = csv.writer(out_f)
            i = 0
            while i < len(rows):
                if rows[i]['Action'] == config['target_action']:
                    path = [config['target_action']]
                    i += 1
                    while i < len(rows) and rows[i]['Action'] != config['target_action']:
                        path.append(rows[i]['Action'])
                        i += 1
                    if len(path) > 1:
                        writer.writerow([' -> '.join(path)])
                else:
                    i += 1


def aggregate_paths(output_dir, config):
    print("Aggregating paths across users...")
    path_counts = defaultdict(int)
    path_users = defaultdict(set)
    action_stats = defaultdict(lambda: {'occurrences': 0, 'users': set()})
    user_paths_dir = os.path.join(output_dir, config['directories']['user_paths'])
    output_files = config['output_files']

    # First pass: collect path statistics
    for path_file in os.listdir(user_paths_dir):
        user = path_file.split('_')[0]
        full_path = os.path.join(user_paths_dir, path_file)
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

    # Write summary of paths
    summary_path = os.path.join(output_dir, output_files['summary'])
    with open(summary_path, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['Path', 'Occurrences', 'Users'])
        for path, count in path_counts.items():
            writer.writerow([path, count, len(path_users[path])])

    print(f"Created summary: {summary_path}")

    # Write detailed action breakdown in the new format
    detailed_path = os.path.join(output_dir, output_files['detailed'])
    with open(detailed_path, 'w', newline='', encoding='utf-8') as f_detail:
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

    print(f"Created detailed action breakdown: {detailed_path}")
    
    return output_files


def generate_plantuml_diagram(output_dir, output_files):
    print("Generating PlantUML class diagram...")
    actions = set()
    connections = set()

    summary_path = os.path.join(output_dir, output_files['summary'])
    with open(summary_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            path = row['Path']
            steps = path.split(' -> ')
            actions.update(steps)
            for i in range(len(steps) - 1):
                connections.add((steps[i], steps[i + 1]))

    plantuml_path = os.path.join(output_dir, output_files['plantuml'])
    with open(plantuml_path, 'w', encoding='utf-8') as f:
        f.write('@startuml\n\n')
        for action in actions:
            f.write(f'class {action} {{}}\n')
        f.write('\n')
        for a1, a2 in connections:
            f.write(f'{a1} --> {a2}\n')
        f.write('\n@enduml\n')

    print(f"Created PlantUML diagram: {plantuml_path}")


def main(input_file, output_dir, config_path):
    # Load configuration
    config = load_config(config_path)
    
    # Process files
    ensure_dirs(output_dir, config)
    split_csv_by_user(input_file, output_dir, config)
    sort_user_file_and_extract_paths(output_dir, config)
    output_files = aggregate_paths(output_dir, config)
    generate_plantuml_diagram(output_dir, output_files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process actions CSV and generate paths.")
    parser.add_argument('--input', type=str, default='output/actions.csv', 
                       help="Input CSV filename")
    parser.add_argument('--output', type=str, default='output', 
                       help="Output directory")
    parser.add_argument('--config', type=str, default='input/config.json',
                       help="Path to configuration file")
    args = parser.parse_args()
    
    main(args.input, args.output, args.config)
