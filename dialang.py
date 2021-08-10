import getopt
import json
import logging
import re
import sys

# logging.root.setLevel(logging.DEBUG)


def main(args: list):
    args = parse_args(args)
    fix_grammar(args["cpython_root"], args["input"])


def parse_args(args: list) -> dict:
    usage = 'Usage: dialang.py -i <input-file> -r <cpython-source-root>'
    try:
        opts, args = getopt.getopt(args, "hi:r:", ["input-file=", "cpython-source-root="])
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)

    values = {
        "cpython_root": "",
        "input": ""
    }
    for opt, arg in opts:
        if opt == '-h':
            print(usage)
            sys.exit()
        if opt in ("-i", "--input-file"):
            try:
                with open(arg, "r") as file:
                    values["input"] = json.load(file)
            except FileNotFoundError:
                print(f"No file found at '{arg}'")
                sys.exit(2)
            except json.decoder.JSONDecodeError:
                print("Json input is invalid. Aborting.")
                sys.exit(2)
        elif opt in ("-r", "--cpython-source-root"):
            values["cpython_root"] = arg
        else:
            print(usage)
            sys.exit(2)

    if not values["input"]:
        print("Input omitted. You can input a valid json with string fields below. "
              "Use ctrl+D to end the input. (you can pass the -h flag to see the command usage)")
        try:
            values["input"] = json.load(sys.stdin)
        except json.decoder.JSONDecodeError:
            print("Json input is invalid. Aborting.")
            sys.exit(2)

    return values


def fix_grammar(cpython_root: str, redirects: dict):
    grammar_filename = cpython_root + "/Grammar/python.gram"
    try:
        with open(grammar_filename, "r+") as grammar_file:
            logging.debug("Opened the grammar file")
            content = grammar_file.read()
            content = apply_grammar_redirects_to_text(content, redirects)
            overwrite_file_content(grammar_file, content)
            print("Successfully applied the grammar changes !")
    except FileNotFoundError:
        print("The CPython source path is invalid.")


def overwrite_file_content(file, content: str):
    file.seek(0)
    file.write(content)
    file.truncate()


def apply_grammar_redirects_to_text(text: str, redirects: dict) -> str:
    for redirect in redirects:
        logging.debug(f"Replacing {redirect} with {redirects[redirect]} for grammar")
        text = apply_grammar_redirect_to_text(text, redirect, redirects)
    return text


def apply_grammar_redirect_to_text(text: str, redirect: str, redirects: dict):
    match = regexp_for_match(redirect)
    repl = regexp_for_repl(redirects[redirect])
    return re.sub(match, repl, text)


def regexp_for_match(match: str):
    return r"'(" + match + r")'"


def regexp_for_repl(repl: str):
    return r"('\1' | '" + repl + r"')"


if __name__ == '__main__':
    main(sys.argv[1:])
