import os
import re
import sys

# Might supplement this with parsing .gitignore
default_ignore = [
    ".idea",
    "node_modules",
    "bin",
    "obj"
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


def last_endpoint() -> Class:
    return res[len(res) - 1]


def last_method() -> Method:
    endpoint = last_endpoint()
    return endpoint.methods[len(endpoint.methods) - 1]


def parse_file(path: str) -> None:
    with open(path) as file:
        lines = "".join(file.readlines())
        classes = re.split(r"class\s+(\w+)", lines, flags=re.MULTILINE)
        i = 0
        while i < len(classes):
            if re.match(r"^\w+$", classes[i]):  # Class name
                res.append(Class(classes[i]))
                i += 1
                if i >= len(classes):
                    continue

                methods = re.split(r"[\w<>]+ (\w+)\s*\(", classes[i], flags=re.MULTILINE)
                j = 0
                while j < len(methods):
                    if re.match(r"^\w+$", methods[j]):  # Method name
                        last_endpoint().methods.append(Method(methods[j]))
                        j += 1
                        if j >= len(methods):
                            continue

                        while methods[j]:
                            query = re.search(r"(SELECT|UPDATE|INSERT|DELETE)(([^\"]*\n?)*)", methods[j], flags=re.MULTILINE)
                            if query is None:
                                break

                            last_method().sql += "\n\n" + methods[j][query.regs[0][0]:query.regs[2][1]]
                            methods[j] = methods[j][query.regs[1][1]:]

                    j += 1

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

    for c in res:
        for m in c.methods:
            m.sql = m.sql.strip("\n\r ")

        c.methods = [x for x in c.methods if x.sql != ""]

    res = [x for x in res if len(x.methods) > 0]

    for c in res:
        print(f"Class: {c.class_name}")
        for m in c.methods:
            print(f'Method: {m.method_name}')
            print(f"SQL: {m.sql}")
