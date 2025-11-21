import argparse

arg_parser = argparse.ArgumentParser(description="Mock DepthAI Output Generator")
arg_parser.add_argument("--file", type=str, required=True, default="spatial_detection_output.txt", help="Input file path")
arg_parser.add_argument("--interval", type=float, default=2.0, help="Interval between outputs in seconds")
args = arg_parser.parse_args()

import time

def mock_depthai_output(file_path, interval):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            print(f"DepthAI Output: {line.strip()}")
            time.sleep(interval)

if __name__ == "__main__":
    mock_depthai_output(args.file, args.interval)
