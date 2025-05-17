import csv
import random
import argparse
from datetime import datetime, timedelta

def generate_csv(filename='actions.csv', num_rows=100):
    users = [f"user{i}" for i in range(1, 6)]
    actions = ['A', 'B', 'C', 'D', 'E']
    start_date = datetime.now()

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Date', 'User', 'Action'])

        for _ in range(num_rows):
            user = random.choice(users)
            date = start_date - timedelta(seconds=random.randint(0, 100000))
            action = random.choice(actions)
            writer.writerow([date.strftime("%Y-%m-%d %H:%M:%S"), user, action])

    print(f"Generated '{filename}' with {num_rows} rows.")

def main():
    parser = argparse.ArgumentParser(description="Generate a sample actions CSV.")
    parser.add_argument('--rows', type=int, default=100, help="Number of rows to generate")
    parser.add_argument('--output', type=str, default='actions.csv', help="Output CSV filename")
    args = parser.parse_args()

    generate_csv(filename=args.output, num_rows=args.rows)

if __name__ == '__main__':
    main()
