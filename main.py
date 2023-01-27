import os
import re
import shutil
import sys
from enum import Enum

# Might supplement this with parsing .gitignore
default_ignore = [
    ".idea",
    "node_modules",
    "bin",
    "obj"
]

keywords = [
    "public",
    "private",
    "protected",
    "internal",
    "async",
    "static",
    "override",
    "virtual",
    "abstract"
]


class Method:
    def __init__(self, method_name: str):
        self.method_name = method_name
        self.sql = ""


class Class:
    def __init__(self, class_name: str):
        self.class_name = class_name
        self.methods: list[Method] = []


res: list[Class] = []


def last_class() -> Class:
    return res[len(res) - 1]


def last_method() -> Method:
    endpoint = last_class()
    return endpoint.methods[len(endpoint.methods) - 1]


class ParseAction(Enum):
    NONE = 0
    CLASS_BODY = 1
    METHOD_BODY = 2


white_space = "\n\r\t "


def parse_file(path: str) -> None:
    with open(path) as file:
        content = "".join(file.readlines())
        i = 0
        action = ParseAction.NONE
        buffer = ""
        is_in_comment = None
        while i < len(content):
            c = content[i]

            if c == '/':  # Check if in comment
                i += 1
                c = content[i]
                if c == '/':
                    is_in_comment = "line"
                if c == '*':
                    is_in_comment = "block"

            if is_in_comment is not None:  # Skip comments
                i += 1
                c = content[i]
                if c == '\n' and is_in_comment == "line":
                    is_in_comment = None
                elif c == '*' and is_in_comment == "block":
                    i += i
                    c = content[i]
                    if c == '/':
                        is_in_comment = None
                continue

            if action == ParseAction.NONE:
                if c in white_space:  # Check word
                    match buffer:
                        case "class":  # Class declaration
                            i += 1
                            c = content[i]
                            while c in white_space:  # Skip whitespace between class keyword and class name
                                i += 1
                                c = content[i]

                            buffer = ""
                            while c not in white_space:
                                buffer += c
                                i += 1
                                c = content[i]

                            res.append(Class(buffer))
                            action = ParseAction.CLASS_BODY

                    buffer = ""
                else:
                    buffer += c

            elif action == ParseAction.CLASS_BODY:
                # Search for type part of member declaration
                if c == '(':  # Method indicator
                    i -= 1
                    c = content[i]
                    while c in white_space:
                        i -= 1
                        c = content[i]

                    buffer = ""
                    while c not in white_space:
                        buffer += c
                        i -= 1
                        c = content[i]

                    i += len(buffer)
                    buffer = buffer[::-1]
                    last_class().methods.append(Method(buffer))
                    buffer = ""
                    action = ParseAction.METHOD_BODY
                else:
                    buffer += c

            elif action == ParseAction.METHOD_BODY:
                if c in white_space:
                    if re.match(r"SELECT|INSERT|UPDATE|DELETE", buffer):  # SQL indicator
                        while True:
                            if c == '"':
                                break

                            buffer += c
                            i += 1
                            c = content[i]

                        buffer = buffer.strip()
                        last_method().sql = buffer

                        buffer = ""
                        action = ParseAction.CLASS_BODY
                    else:
                        buffer = ""
                else:
                    buffer += c

            i += 1


def search_files(dir_path: str) -> None:
    content = os.listdir(dir_path)
    for path in content:
        full_path = os.path.join(dir_path, path)
        if os.path.isdir(full_path) and path not in default_ignore:
            search_files(full_path)
        elif os.path.isfile(full_path) and path.endswith(".cs"):
            parse_file(full_path)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Need to specify path to ASP.NET Core project")
        exit(1)

    root = sys.argv[1]
    search_files(root)

    for _class in res:
        _class.class_name = re.sub(r"(\w+)Controller$", r"\1", _class.class_name)
        _class.methods = [x for x in _class.methods if x.sql != ""]
        for m in _class.methods:
            m.sql = re.sub(r"\{(\w+)[^}]*}", r":\1", m.sql.strip("\n\r "), flags=re.MULTILINE)

    res = [x for x in res if len(x.methods) > 0]

    dir_name = os.path.basename(root)
    dest = os.path.join(root, "..", sys.argv[2], dir_name)
    shutil.rmtree(dest)
    os.makedirs(dest)

    for _class in res:
        class_path = os.path.join(dest, _class.class_name)
        os.mkdir(class_path)

        for method in _class.methods:
            file_path = os.path.join(class_path, method.method_name)
            print(f'Writing to file {file_path}:\n{method.sql}\n')
            with open(file_path + ".sql", 'x') as file:
                file.write(method.sql + '\n')

    print("Application executed successfully")
