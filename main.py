import re

from redirects import redirects

cpython_root = ""


def fix():
    fix_grammar()
    register_keywords()


def fix_grammar():
    grammar_filename = cpython_root + "Grammar/python.gram"
    with open(grammar_filename, "r+") as grammar_file:
        print("Opened the grammar file")
        content = grammar_file.read()
        content = apply_grammar_redirects_to_text(content)
        overwrite_file_content(grammar_file, content)
        print("Finished fixing the grammar")


def register_keywords():
    pass


def overwrite_file_content(file, content):
    file.seek(0)
    file.write(content)
    file.truncate()


def apply_grammar_redirects_to_text(text):
    for redirect in redirects:
        print(f"Replacing {redirect} with {redirects[redirect]} for grammar")
        match = regexp_for_match(redirect)
        repl = regexp_for_repl(redirects[redirect])
        text = re.sub(match, repl, text)
    return text


def regexp_for_match(match):
    return r"'(" + match + r")'"


def regexp_for_repl(repl):
    return r"('\1' | '" + repl + r"')"