#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "fuzzywuzzy",
#     "python-Levenshtein"
# ]
# ///
import sys
import os
import random
import string
import argparse
from subprocess import call
from fuzzywuzzy import fuzz

FYI_PATH = os.path.expanduser(".fyi")


def pretty_list(mylist):
    """Format a list into a pretty string with indices."""
    out = []
    for i, elem in enumerate(mylist):
        line = "["
        if len(mylist) > 9 and i < 9:
            line += " "
        line += "{}] {}".format(i + 1, elem)
        out.append(line.strip())
    return "\n".join(out)


def generate_random_key(length):
    """Generate a random string of lowercase letters and digits."""
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(length)
    )


def make_fyi_folder():
    if not os.path.exists(FYI_PATH):
        os.makedirs(FYI_PATH)


def open_vim(file_path):
    call(["vim", file_path])


def display_file_content(file_path):
    with open(file_path) as fyifile:
        fyilines = fyifile.readlines()
        # remove tags line at end of file
        if fyilines and all([t[0] == "#" for t in fyilines[-1].split()]):
            fyilines.pop()
        print("\n".join(fyilines[2:]).strip())


def open_vim_with_random_string():
    """Create a new FYI file with a random name and open it in Vim."""
    random_string = generate_random_key(16)
    new_path = os.path.join(FYI_PATH, f"{random_string}.fyi")
    open_vim(new_path)


def find_fyi(query_string):
    results = []
    for filename in os.listdir(FYI_PATH):
        if filename.endswith(".fyi"):
            file_path = os.path.join(FYI_PATH, filename)
            with open(file_path) as fyifile:
                first_line = fyifile.readline()
                rest = fyifile.readlines()
                tags = [t[1:] for t in rest[-1].split() if t[0] == "#"]
                r = fuzz.token_set_ratio(
                    query_string, first_line + " " + " ".join(tags)
                )
                if r > 73:
                    results.append(
                        {"first_line": first_line.strip(), "file_path": file_path}
                    )
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", help="query for FYIs")
    parser.add_argument(
        "idx", nargs="?", type=int, help="with query, display an FYI by the index"
    )
    args = parser.parse_args()

    if not (args.query or args.idx):  # fyi
        make_fyi_folder()
        open_vim_with_random_string()
    elif args.query and not args.idx:  # fyi "my search terms"
        results = find_fyi(args.query)
        if len(results) == 0:
            print("\033[1m:: no results ::\033[0m")
        else:
            print("\033[1m:: results ::\033[0m")
            print(pretty_list([result["first_line"] for result in results]))
    elif args.query and args.idx:  # fyi "my search terms" 1
        results = find_fyi(args.query)
        if 0 <= args.idx - 1 < len(results):
            chosen_result = results[args.idx - 1]
            file_path = chosen_result["file_path"]
            print("\033[1m:: {} ::\033[0m".format(file_path))
            display_file_content(file_path)
        else:
            print("\033[1m:: invalid index ::\033[0m")


if __name__ == "__main__":
    main()