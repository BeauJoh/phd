#
# Copyright 2017 Chris Cummins <chrisc.101@gmail.com>.
#
# This file is part of DeepSmith.
#
# DeepSmith is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# DeepSmith is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# DeepSmith.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Parser for dsmith

Attributes:
    __help__ (str): REPL help string.
    __available_commands__ (str): Help string for available commands.
"""
import datetime
import humanize
import logging
import math
import os
import progressbar
import random
import re
import sys
import traceback

from collections import namedtuple
from labm8 import fs

import dsmith
from dsmith import Colors, langs

_lang_str = f"{Colors.RED}<lang>{Colors.END}{Colors.BOLD}"
_generator_str = f"{Colors.GREEN}<generator>{Colors.END}{Colors.BOLD}"
_testbed_str = f"{Colors.PURPLE}<testbed>{Colors.END}{Colors.BOLD}"
_num_str = f"{Colors.BLUE}<number>{Colors.END}{Colors.BOLD}"

__available_commands__ = f"""\
  {Colors.BOLD}describe [all]{Colors.END}
    Provide an overview of stored data.

  {Colors.BOLD}describe {_lang_str} {{\
{Colors.GREEN}generators{Colors.END}{Colors.BOLD},\
{Colors.PURPLE}testbeds{Colors.END},\
programs,testcases,results}}{Colors.END}
    Provide details about available generators, testbeds, generated
    programs, testcases, or results.

  {Colors.BOLD}make [[up to] {_num_str}] {_lang_str} programs [using {_generator_str}]{Colors.END}
    Generate the specified number of programs. If no generator is specified,
    default to dsmith.

  {Colors.BOLD}make {_lang_str} [{_generator_str}] testcases{Colors.END}
    Prepare testcases from programs.

  {Colors.BOLD}run {_lang_str} [{_generator_str}] testcases [on {_testbed_str}] [{{with,without}} optimizations]{Colors.END}
    Run testcases. If no generator is specified, run testcases from all
    generators. If no testbed is specified, use all available
    testbeds. If optimizations are not specified, run both.

  {Colors.BOLD}difftest {_lang_str} [{_generator_str}] results{Colors.END}
    Compare results across devices.

  {Colors.BOLD}test{Colors.END}
    Run the self-test suite.

  {Colors.BOLD}version{Colors.END}
    Print version information.

  {Colors.BOLD}exit{Colors.END}
    End the session.\
"""


__help__ = f"""\
This is the DeepSmith interactive session. The following commands are available:

{__available_commands__}
"""


class UnrecognizedInput(ValueError):
    pass


def _hello_func(file=sys.stdout):
    print("Hi there!", file=file)


def _help_func(file=sys.stdout):
    print(__help__, file=file)


def _version_func(file=sys.stdout):
    print(dsmith.__version_str__, file=file)


def _test_func(file=sys.stdout):
    import dsmith.test
    dsmith.test.testsuite()


def _exit_func(*args, **kwargs):
    file = kwargs.pop("file", sys.stdout)

    farewell = random.choice([
        "Have a nice day!",
        "Over and out.",
        "God speed.",
        "See ya!",
        "See you later alligator.",
    ])
    print(f"{Colors.END}{farewell}", file=file)
    sys.exit()


def _describe_programs_func(lang, file=sys.stdout):
    for generator in lang.generators:
        num = humanize.intword(generator.num_programs())
        sloc = humanize.intword(generator.sloc_total())
        print(f"You have {Colors.BOLD}{num} {generator.__name__}{Colors.END} "
              f"programs, total {Colors.BOLD}{sloc}{Colors.END} SLOC",
              file=file)


def _make_programs(lang: langs.Language, generator: langs.Generator,
                   n: int, up_to: bool=False, file=sys.stdout):
    up_to_val = n if up_to else math.inf
    n = math.inf if up_to else n
    generator.generate(n=n, up_to=up_to_val)


def _make_testcases(lang, generator):
    raise NotImplementedError


def _run_func(*args, **kwargs):
    raise NotImplementedError


def _difftest_func(*args, **kwargs):
    raise NotImplementedError


def execute(statement: str, file=sys.stdout) -> None:
    """
    Pseudo-natural language command parsing.
    """
    if not isinstance(statement, str): raise TypeError

    # parsing is case insensitive
    statement = re.sub("\s+", " ", statement.strip().lower())
    components = statement.split(" ")

    if not statement:
        return

    # Parse command modifiers:
    if components[0] == "debug":
        statement = re.sub(r'^debug ', '', statement)
        with dsmith.debug_scope():
            return execute(statement, file=file)
    elif components[0] == "verbose":
        components = components[1:]
        statement = re.sub(r'^verbose ', '', statement)
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                            level=logging.INFO)

    csv = ", ".join(f"'{x}'" for x in components)
    logging.debug(f"parsing input [{csv}]")

    # Commands parser:
    if len(components) == 1 and re.match(r'(hi|hello|hey)', components[0]):
        return _hello_func(file=file)

    if len(components) == 1 and re.match(r'(exit|quit)', components[0]):
        return _exit_func(file=file)

    if len(components) == 1 and components[0] == "help":
        return _help_func(file=file)

    if len(components) == 1 and components[0] == "version":
        return _version_func(file=file)

    if len(components) == 1 and components[0] == "test":
        return _test_func(file=file)

    if components[0] == "describe":
        programs_match = re.match(r'describe ((?P<lang>\w+) )?programs', statement)

        if programs_match:
            lang = langs.mklang(programs_match.group("lang"))

            return _describe_programs_func(lang=lang, file=file)
        else:
            raise UnrecognizedInput

    if components[0] == "make":
        programs_match = re.match(r'make ((?P<up_to>up to )?(?P<number>\d+) )?(?P<lang>\w+) program(s)?( using (?P<generator>\w+))?', statement)
        testcases_match = re.match(r'make (?P<lang>\w+) ((?P<generator>\w+) )?testcases', statement)

        if programs_match:
            number = int(programs_match.group("number") or 0) or math.inf
            lang = langs.mklang(programs_match.group("lang"))
            generator = lang.mkgenerator(programs_match.group("generator"))

            return _make_programs(
                lang=lang, generator=generator, n=number,
                up_to=True if programs_match.group("up_to") else False,
                file=file)

        elif testcases_match:
            lang = testcases_match.group("lang")
            generator = testcases_match.group("generator")

            return _make_testcases(lang=language, generator=generator, file=file)

        else:
            raise UnrecognizedInput

    if components[0] == "run":
        return _run_func(file=file)

    if components[0] == "difftest":
        return _difftest_func(file=file)

    raise UnrecognizedInput


def _user_message_with_stacktrace(exception):
        # get limited stack trace
        def _msg(i, x):
            n = i + 1

            filename = fs.basename(x[0])
            lineno = x[1]
            fnname = x[2]

            loc = "{filename}:{lineno}".format(**vars())
            return "      #{n}  {loc: <18} {fnname}()".format(**vars())

        _, _, tb = sys.exc_info()
        NUM_ROWS = 5  # number of rows in traceback

        trace = reversed(traceback.extract_tb(tb, limit=NUM_ROWS+1)[1:])
        stack_trace = "\n".join(_msg(*r) for r in enumerate(trace))
        typename = type(exception).__name__

        print(f"""
======================================================================
💩  Fatal error!
{exception} ({typename})

  stacktrace:
{stack_trace}

Please report bugs at <https://github.com/ChrisCummins/dsmith/issues>\
""", file=sys.stderr)


def run_command(command: str, file=sys.stdout) -> None:
    try:
        execute(command, file=file)
    except UnrecognizedInput as e:
        print("😕  I don't understand. "
              "Type 'help' for available commands.", file=file)
        if os.environ.get("DEBUG"):
            raise e
    except NotImplementedError as e:
        print("🤔  I don't know how to do that (yet).", file=file)
        if os.environ.get("DEBUG"):
            raise e
    except Exception as e:
        _user_message_with_stacktrace(e)
        if os.environ.get("DEBUG"):
            raise e


def repl(file=sys.stdout) -> None:
    hour = datetime.datetime.now().hour

    greeting = "Good evening."
    if hour > 4:
        greeting = "Good morning."
    if hour > 12 and hour < 18:
        greeting = "Good afternoon."

    print(greeting, "Type 'help' for available commands.", file=file)

    try:
        while True:
            sys.stdout.write(f"{Colors.BOLD}> ")
            choice = input()
            sys.stdout.write(Colors.END)
            sys.stdout.flush()

            # Strip '#' command, and split ';' separated commands
            commands = choice.split("#")[0].split(";")

            for command in commands:
                run_command(command, file=file)

    except KeyboardInterrupt:
        print("", file=file)
        _exit_func(file=file)
