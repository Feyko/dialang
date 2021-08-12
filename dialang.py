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


def changelog(write: dict = None):
    if write is None:
        with open(".dialang/grammar_changelog.json", 'r') as changelog_file:
            return json.load(changelog_file)
    else:
        with open(".dialang/grammar_changelog.json", 'w') as changelog_file:
            return json.dump(write, changelog_file)


def fix_grammar(cpython_root: str, redirects: dict):

    previous_changes = changelog()

    grammar_filename = cpython_root + "/Grammar/python.gram"
    try:
        with open(grammar_filename, "r+") as grammar_file:
            logging.debug("Opened the grammar file")
            content = grammar_file.read()
            content, new_changes = apply_grammar_redirects_to_text(content, redirects, previous_changes)
            overwrite_file_content(grammar_file, content)
            changelog(new_changes)
            logging.debug("Successfully applied the grammar changes!")
            print("Successfully applied the grammar changes!")
    except FileNotFoundError:
        print("The CPython source path is invalid.")


def overwrite_file_content(file, content: str):
    file.seek(0)
    file.write(content)
    file.truncate()


def apply_grammar_redirects_to_text(text: str, redirects: dict, history: dict) -> tuple[str, dict]:
    for old in redirects:
        new = redirects[old]
        text_to_replace = old
        if old in history:  # read: if this has already been changed before
            # we will need to replace the current changed version of this redirect, not the original
            # f. e. if we have already changed 'del' to ('del' | 'yeet'), to change 'del' again, we need to replace
            # ('del' | 'yeet') with our new definition
            if history[old]:
                text_to_replace = history[old]


        logging.debug(f"Replacing {text_to_replace} with {[old] + new} for grammar")
        if new:
            text = add_redirect_list_to_text(text, text_to_replace, new)
        else:
            text = reset_redirect_in_text(text, text_to_replace, old)

        history.update(redirects)
    return text, history


def add_redirect_list_to_text(text: str, redirect: str, redirects: list):
    match = regexp_for_match(redirect)
    repl = regexp_for_replace(redirects, redirect)
    return re.sub(match, repl, text)


def reset_redirect_in_text(text: str, current: list, original: str):
    match = regexp_for_match(f"('{stringify_additions([original] + current)}')")
    repl = f"'{original}'"
    return re.sub(match, repl, text)


def stringify_additions(additions: list):
    return "' | '".join([f"{word}" for word in additions])


def regexp_for_match(match: str):
    if "|" in match:
        return r"(" + re.sub(r"([(|)])+", r"\\\1", match) + r")"  # use the regex to format the regex
    else:
        return r"'(" + match + r")'"


def regexp_for_replace(additions: list, original: str):
    return r"('\1' | '" + stringify_additions(additions) + r"')" if additions else f"'{original}'"


if __name__ == '__main__':
    main(sys.argv[1:])
