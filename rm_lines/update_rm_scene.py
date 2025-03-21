import atexit
import os
import re
import shutil
import subprocess
import tempfile
import time
import venv
from itertools import chain
from typing import List, Tuple, Dict

import colorama
from colorama import Fore
from slashr import SlashR

colorama.init()

WORK_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(WORK_DIR, ".cached")
REPO_URL = "https://github.com/ricklupton/rmscene.git"
REPO_CLONE_DIR = os.path.join(CACHE_DIR, "rmscene")
MODIFICATIONS_DIR = tempfile.mkdtemp()
VENV_DIR = os.path.join(CACHE_DIR, ".venv")
EXTRA_PACKAGES = ("poetry", "black")
VENV_BIN_DIR = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin")
PIP_EXECUTABLE = os.path.join(VENV_BIN_DIR, "pip" + (".exe" if os.name == "nt" else ""))
PYTHON_EXECUTABLE = os.path.join(VENV_BIN_DIR, "python" + (".exe" if os.name == "nt" else ""))
SOURCE_DIR = os.path.join(MODIFICATIONS_DIR, "src", "rmscene")
TESTS_DIR = os.path.join(MODIFICATIONS_DIR, "tests")
TAB = '    '
DEBUG = False

atexit.register(lambda: shutil.rmtree(MODIFICATIONS_DIR))

os.environ['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'  # Disable pip version check

EXTRA_VALUES = {
    # 'SceneInfo': (
    #     ('page_size', 'tp.Tuple[int, int]', None),
    # )
}


def print_stage(stage):
    print(f"{Fore.CYAN}{'=' * 5} {stage} {'=' * 5}{Fore.RESET}", flush=True)
    time.sleep(.1)


def run_poetry_modifier(line):
    if line.startswith('python = '):
        return 'python = "^3.9"'
    if 'poetry.dev-dependencies' in line:
        return line.replace('poetry.dev-dependencies', 'poetry.group.dev.dependencies')
    return line


def remove_from(line, *imports):
    _, module, _, sub_modules_line = line.split(' ', 3)
    sub_modules = [
        stripped
        for sub_module in sub_modules_line.split(',')
        if (stripped := sub_module.strip()) not in imports
    ]
    return f'from {module} import {", ".join(sub_modules)}'


def run_import_replacers(line):
    if 'dataclasses' in line:
        return remove_from(line, 'KW_ONLY')

    return line


def run_tagged_block_common_modifiers(line):
    if line.strip().startswith('Byte4'):
        line = f"{line}\n{line.replace('4', '2')}"
    return line


def run_line_class_modifier(line):
    def add_rgba_color():
        nonlocal line
        line = (
            f"{TAB}if color_id == si.PenColor.HIGHLIGHT:\n"
            f"{TAB}{TAB}try:\n"
            f"{TAB}{TAB}{TAB}rgba_color = stream.read_color(8)\n"
            f"{TAB}{TAB}except UnexpectedBlockError:\n"
            f"{TAB}{TAB}{TAB}rgba_color = None\n"
            f"{TAB}else:\n"
            f"{TAB}{TAB}rgba_color = None\n{line}"
        )

    if line.strip().startswith('return si.Line('):
        line = line.replace(
            'return si.Line(',
            'return si.Line(rgba_color, ',
        )
        add_rgba_color()
    if line.strip().startswith('return si.GlyphRange('):
        line = line.replace(
            'return si.GlyphRange(',
            'return si.GlyphRange(rgba_color, ',
        )
        add_rgba_color()

    return line


def run_extra_reader_modifier(line):
    if line.strip().endswith('## Read simple values'):
        line = (
            f"{line}\n"

            # add read color
            f"{TAB}def read_color(self, index: int) -> tp.Tuple[int, ...]:\n"
            f"{TAB}{TAB}self.data.read_tag(index, TagType.Byte4)\n"
            f"{TAB}{TAB}color_bytes = self.data.read_bytes(4)[::-1]\n"
            f"{TAB}{TAB}# reMarkable uses a ARGB format, convert to RGBA for ease of use\n"
            f"{TAB}{TAB}return tuple(int(b) for b in (color_bytes[1], color_bytes[2], color_bytes[3], color_bytes[0]))"
        )

    return line


def run_scene_stream_modifier(line):
    if line.strip().startswith('elif isinstance(b, RootTextBlock):'):
        # Add page size block to tree
        line = (
            f'{TAB}{TAB}elif isinstance(b, SceneInfo):\n'
            f'{TAB}{TAB}{TAB}tree.scene_info = b\n'
            f'{line}'
        )
    return line


def run_scene_items_modifier(line):
    if line.strip().startswith('color: PenColor'):
        line = f"{TAB}rgba_color: tp.Optional[tp.Tuple[int, ...]]\n{line}"
    return re.sub(r'\[([^\|]+)\s\|\s([^\]]+)\]', r'[tp.Union[\1, \2]]', line)


def run_scene_tree_modifier(line):
    if line.strip().startswith('self.root '):
        line = (
            f"{line}\n"
            f"{TAB}{TAB}self.scene_info: tp.Optional['SceneInfo'] = None"
        )
    if 'import scene_items' in line:
        line = (
            f'{line}\n'
            f'if tp.TYPE_CHECKING:\n'
            f'{TAB}from .scene_stream import SceneInfo'
        )
    return line


def run_test_modifiers(line):
    if line.endswith('GlyphRange('):
        return f'{line}\nrgba_color=None,'
    if line.endswith('Line('):
        return f'{line}\nrgba_color=None,'
    return line


def dataclass_join_base(base_items, items):
    internal_items = {}
    for key, *item in base_items:
        internal_items[key] = item
    for key, *item in items:
        internal_items[key] = item

    return sorted(((key, *value) for key, value in internal_items.items()), key=lambda x: x[2] is not None)


def subtractive_join_base(base_items, items):
    internal_items = {}
    for key, *item in items:
        internal_items[key] = item
    for key, *item in base_items:
        if key in internal_items:
            del internal_items[key]

    return ((key, *value) for key, value in internal_items.items())


def dataclass_replacer(code: str):
    classes = []
    lines = (line for line in code.splitlines())
    base_args: Dict[str, List[Tuple[str, str, str]]] = {
        'ABC': []
    }
    base_kwargs: Dict[str, List[Tuple[str, str, str]]] = {
        'ABC': []
    }
    while (line := next(lines, None)) is not None:
        class_lines = []
        in_between_lines = []
        var_lines = []
        if line.startswith('@dataclass') or line.endswith('SceneItemBlock):'):
            if line.startswith('@dataclass'):
                class_lines.append(line)  # @dataclass
                class_definition = next(lines)
            else:
                class_definition = line
            class_lines.append(class_definition)  # class ...
            while (line := next(lines, None)) is not None:  # Detect tab
                class_lines.append(line)
                if len(line) < 1:
                    line = next(lines)
                    if len(line) < 1:
                        break
                    else:
                        class_lines.append(line)
                if line.startswith('\t\t') or line.startswith(f'{TAB}{TAB}'):
                    in_between_lines.append(line)
                    continue
                elif not (line.startswith('\t') or line.startswith(TAB)):
                    break
                line_stripped = line.strip()
                if line_stripped.startswith("def") or line_stripped.startswith("@"):  # Detect new method or decorator
                    in_between_lines.append(line)
                    continue
                if line_stripped.startswith('"') or line_stripped.startswith("#"):
                    in_between_lines.append(line)
                    continue
                if line_stripped.split(':')[0].isupper():
                    in_between_lines.append(line)
                    continue
                var_lines.append(line_stripped)
        else:
            continue

        class_remade_lines = [
            class_definition,
            *in_between_lines
        ]
        args = []
        kwargs = []

        kwarg_only = False

        if DEBUG:
            print(var_lines)

        for var in var_lines:
            var_name, var_type = [part.strip() for part in var.split(':')]
            if '=' in var_type:
                var_type, default = var_type.split('=')
                var_type = var_type.strip()
                default_value = default.strip()
            else:
                default_value = None
            if var_type == 'KW_ONLY':
                kwarg_only = True
                continue
            if kwarg_only:
                kwargs.append((var_name, var_type, default_value))
            else:
                args.append((var_name, var_type, default_value))

        if is_base := not class_definition.endswith('):'):  # Doesn't inherit anything
            base_class_name = class_definition.split(':')[0].split()[-1].strip()
            class_name = base_class_name
            base_args[base_class_name] = args.copy()
            base_kwargs[base_class_name] = kwargs.copy()
            args.clear()
            kwargs.clear()
        else:
            initial_base_class_name = class_definition.split('(')[1].split(')')[0].strip()  # Get the inherited class
            class_name = class_definition.split(':')[0].split()[-1].split('(')[0].strip()  # Get the class name
            if initial_base_class_name == 'ABC' or class_name == 'SceneItemBlock':  # If it's an abstract class, treat it as a base class
                base_class_name = class_name

                base_args[base_class_name] = args.copy()
                base_kwargs[base_class_name] = kwargs.copy()

                if class_name != 'SceneItemBlock':
                    args.clear()
                    kwargs.clear()
                    is_base = True
                else:
                    base_class_name = initial_base_class_name  # Restore the base to complete this new base
            else:
                base_class_name = initial_base_class_name

        if extra_values := EXTRA_VALUES.get(class_name):
            args.extend(extra_values)

        if not (args or kwargs or is_base):  # skip if no args, kwargs and not a base class
            continue

        args_code = ', '.join(
            f"{arg_name}: {arg_type} = {default_value}"
            if default_value else f"{arg_name}: {arg_type}"
            for arg_name, arg_type, default_value in dataclass_join_base(
                base_args[base_class_name], args
            )
        )  # Generate the args code for the __init__ method
        kwargs_code = ', '.join(
            f"{kwarg_name}: {kwarg_type} = {default_value}"
            if default_value else f"{kwarg_name}: {kwarg_type}"
            for kwarg_name, kwarg_type, default_value in dataclass_join_base(
                base_kwargs[base_class_name], kwargs
            )
        )  # Generate the kwargs code for the __init__ method
        class_remade_lines.append(
            f"{TAB}def __init__(self, {args_code + ', ' if args_code else ''}{'*, ' + kwargs_code if kwargs_code else ''}):")

        # Generate the __init__ method
        if not is_base:
            base_args_code = ', '.join(arg_name for arg_name, _, _ in base_args[base_class_name])
            base_kwargs_code = ', '.join(
                f'{kwarg_name} = {kwarg_name}' for kwarg_name, _, _ in base_kwargs[base_class_name])
            class_remade_lines.append(
                f"{TAB}{TAB}super().__init__({base_args_code + ', ' if base_args_code else ''}{base_kwargs_code})")
            # Call the super class __init__ method

        for var_name, var_type, _ in (
                base_args[base_class_name] + base_kwargs[base_class_name]) \
                if is_base else chain(
            subtractive_join_base(base_args[base_class_name], args),
            subtractive_join_base(base_kwargs[base_class_name], kwargs)
        ):
            class_remade_lines.append(f"{TAB}{TAB}self.{var_name}: {var_type} = {var_name}")

        class_code = '\n'.join(class_lines)
        class_remade_code = '\n'.join(class_remade_lines)

        classes.append((class_code, class_remade_code))

    for class_code, class_remade_code in classes:
        code = code.replace(class_code, class_remade_code)
        if DEBUG:
            print(
                f"{Fore.LIGHTBLACK_EX}{'=' * 30}{Fore.RED}\n"

                f"{class_code}\n"

                f"{Fore.CYAN}{'=' * 30}{Fore.GREEN}\n"

                f"{class_remade_code}\n"

                f"{Fore.LIGHTBLACK_EX}{'=' * 30}{Fore.RESET}"
            )
    code = code.replace('@dataclass', '')

    return code


class WaitNicely:
    def __init__(self, start_message, end_message):
        self.start_message = start_message
        self.end_message = end_message
        self.sr = SlashR(False)

    def __enter__(self):
        self.sr.__enter__()
        self.sr.print(f'{Fore.YELLOW}{self.start_message}{Fore.RESET}')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sr.print(f'{Fore.GREEN}{self.end_message} ✔{Fore.RESET}')
        self.sr.__exit__(exc_type, exc_val, exc_tb)


class OpenModify:
    def __init__(self, file):
        self.file = file
        filename = file.replace(MODIFICATIONS_DIR, '').lstrip(os.path.sep)
        self.wait_nicely = WaitNicely(f"Modifying {filename}", f"Modified {filename}")
        with open(file, 'r') as f:
            self.old_data = f.read()

    def __enter__(self):
        self.f = open(self.file, 'w')
        self.wait_nicely.__enter__()
        return self.f, self.old_data

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.close()
        self.wait_nicely.__exit__(exc_type, exc_val, exc_tb)


# ========================================
print_stage("Clone the rmscene repo")
# ========================================
os.makedirs(CACHE_DIR, exist_ok=True)
if not os.path.exists(REPO_CLONE_DIR):
    subprocess.run(["git", "clone", REPO_URL, REPO_CLONE_DIR], stderr=subprocess.STDOUT)
else:
    subprocess.run(["git", "-C", REPO_CLONE_DIR, 'fetch', '--all'], stderr=subprocess.STDOUT)
    subprocess.run(["git", "-C", REPO_CLONE_DIR, 'reset', '--hard', 'origin/main'], stderr=subprocess.STDOUT)
os.chdir(MODIFICATIONS_DIR)

# ========================================
print_stage("Setup the environment")
# ========================================
with WaitNicely("Creating virtual environment", f"Created virtual environment"):
    if not os.path.exists(PYTHON_EXECUTABLE) and not os.path.exists(PIP_EXECUTABLE):
        if os.path.exists(VENV_DIR):
            shutil.rmtree(VENV_DIR)
        venv.create(VENV_DIR, with_pip=True)

packages = ', '.join(EXTRA_PACKAGES)
with WaitNicely(f"Installing {packages}", f"Installed {packages}"):
    subprocess.run([PIP_EXECUTABLE, "install", *EXTRA_PACKAGES], stdout=subprocess.PIPE)
shutil.copytree(REPO_CLONE_DIR, MODIFICATIONS_DIR, dirs_exist_ok=True)

# ========================================
print_stage("Running modifications")
# ========================================
with OpenModify(os.path.join(MODIFICATIONS_DIR, "pyproject.toml")) as (f, old):
    final = '\n'.join(
        run_poetry_modifier(line)
        for line in old.splitlines()
    )

    f.write(final)

with OpenModify(os.path.join(SOURCE_DIR, 'tagged_block_reader.py')) as (f, old):
    imports_fixed = '\n'.join(
        run_extra_reader_modifier(run_import_replacers(line))
        for line in old.splitlines()
    )

    final = dataclass_replacer(imports_fixed)

    f.write(final)

with OpenModify(os.path.join(SOURCE_DIR, 'scene_stream.py')) as (f, old):
    imports_fixed = '\n'.join(
        run_scene_stream_modifier(run_line_class_modifier(run_import_replacers(line)))
        for line in old.splitlines()
    )

    final = dataclass_replacer(imports_fixed)

    f.write(final)

with OpenModify(os.path.join(SOURCE_DIR, 'scene_items.py')) as (f, old):
    final = '\n'.join(
        run_scene_items_modifier(line)
        for line in old.splitlines()
    )

    f.write(final)

with OpenModify(os.path.join(SOURCE_DIR, 'scene_tree.py')) as (f, old):
    final = '\n'.join(
        run_scene_tree_modifier(line)
        for line in old.splitlines()
    )

    f.write(final)

with OpenModify(os.path.join(SOURCE_DIR, 'tagged_block_common.py')) as (f, old):
    final = '\n'.join(
        run_tagged_block_common_modifiers(line)
        for line in old.splitlines()
    )

    f.write(final)

for item in os.listdir(TESTS_DIR):
    location = os.path.join(TESTS_DIR, item)
    if os.path.isdir(location):
        continue
    with OpenModify(location) as (f, old):
        final = '\n'.join(
            run_test_modifiers(line)
            for line in old.splitlines()
        )

        f.write(final)

# ========================================
print_stage("Checking modifications")
# ========================================

with WaitNicely("Linting", "Linted the code"):
    subprocess.run([PYTHON_EXECUTABLE, "-m", "black", MODIFICATIONS_DIR], stderr=subprocess.DEVNULL)

# ========================================
print_stage("Running tests")
# ========================================
with WaitNicely("Preparing poetry", "Prepared poetry"):
    subprocess.run([PYTHON_EXECUTABLE, "-m", "poetry", "lock"], stdout=subprocess.DEVNULL)
    subprocess.run([PYTHON_EXECUTABLE, "-m", "poetry", "install"], stdout=subprocess.DEVNULL)

with WaitNicely("Running tests", "Finished running tests"):
    tests_output = subprocess.run([PYTHON_EXECUTABLE, "-m", "poetry", "run", "pytest"], stdout=subprocess.PIPE
                                  ).stdout.decode()

if 'error' in tests_output.lower():
    print(f"{Fore.RED}Tests had some errors{Fore.RESET}")
    print_stage("Please fix the modifications before continuing")
    print(f"{Fore.RED}{tests_output}{Fore.RESET}")

# ========================================
print_stage("Copy sources")
# ========================================
shutil.copytree(os.path.join(MODIFICATIONS_DIR, "src", "rmscene"), os.path.join(WORK_DIR, "rmscene"),
                dirs_exist_ok=True)
shutil.copy(os.path.join(MODIFICATIONS_DIR, "LICENSE"), os.path.join(WORK_DIR, "rmscene", "LICENSE"))
