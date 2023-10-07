"""
simplestash.py - a minimalist version of tabstash.py
Stores links in a YAML file called simplelinks.json

Input is in this syntax:
> #Link Name:https://github.com

TODO: Need to implement TUI colors with termcolors
TODO: Implement search function for quickly finding a link
TODO: Add "edit" function for renaming the link/label
TODO: Catch CTRL C keyboard exit event and handle it gracefully
"""
import os
import sys
from datetime import datetime
import re
import yaml
import clipboard
from yaml.loader import SafeLoader
from simple_term_menu import TerminalMenu

# Variables are stored here
home_dir = os.path.expanduser("~")
app_database_file = os.path.join(home_dir, ".simplestash.yml")
app_logfile = os.path.join(home_dir, ".simplestash.log")
check_symbol = "(✓)"
bullet_symbol = "•"


# Classes are here
class Format:
    end = '\033[0m'
    underline = '\033[4m'


def help_handler(error=""):
    help_message = """
Welcome to simplestash! You are viewing its built-in help utility!
{}

Simplestash accepts these command-line arguments:

    python simplestash.py new
        Creates a new link using the syntax #link-name:https://your-link.com
    python simplestash.py list
        Lists the links you've already stashed
    python simplestash.py cp
        Copies the URL of a link
    python simplestash.py reset
        Deletes debug log and database files
    python simplestash.py viewlog
        Shows the location of the logfile and how to view it

Simplestash saves its configuration data in ~/.simplestash.yml.
You may view its debug log at ~/.simplestash.log to troubleshoot your error
    """.format(error)
    if error == "":
        split_message = help_message.splitlines()
        split_message.pop(3)
        rejoined_message = "\n".join(split_message)
        print(rejoined_message)
    else:
        print(help_message)

"""
Enter your new link here

"""

def get_yes_no(result):
    while result not in ("Y", "y", "N", "n"):
        print(f"Your answer of '{result}' is not a valid option. ")
        print("Try again. Please enter Y, y, N, or n.")
        result = input("[Y/N]: ")
    return result


def regenerate_yaml():
    print("Are you sure you want to generate a new database file?")
    print("This will overwrite your existing database! Only do this if your existing database is missing or broken!")
    result = input("[Y/N]: ")
    if get_yes_no(result) in ("Y", "y"):
        print("Generating new database...")
        # We generate only a new config, not a new debug
        # log
        log("New database generated and previous database erased")
        exit_app(0)
    else:
        print("\nDatabase regeneration aborted. Simplestash will close now.")
        exit_app(0)


def read_config_file():
    if os.path.exists(app_database_file) is False:
        print("Hello there! Your simplestash database is missing or hasn't been created yet.")
        print("If you're starting simplestash for the first time, this is normal.")
        print("Is this your first time using simplestash?")
        result = input("[Y/N]: ")
        if get_yes_no(result) in ("Y", "y"):
            print("\nThat's great! Just a few things to set up...\n")
            # Then do the first time stuff
            print("Setting up the debug log...")
            with open(app_logfile, "w") as f:
                f.write(f"This is the simplestash log, created at {current_time()}.\n")
            print(f"{check_symbol} Debug log created at {app_logfile}!\n")
            print("Setting up database...")
            # This is the default database
            # firstlaunch is False because we don't want to show
            # the onboarding wizard the second time
            app_data = {"firstlaunch": False, "links": {}}
            print(f"{check_symbol} Database created!\n")
            print("Setting up database YAML file...")
            with open(app_database_file, "w") as f:
                yaml.dump(app_data, f)
            print(f"{check_symbol} Database file created at {app_database_file}!\n")
            begin_log()
            print("Great! You're all set.")
            print("Try running 'python simplestash.py new' to add your first link.")
            exit_app(0)
        else:
            # Presumably, if the user doesn't have the app
            # data file AND it isn't the first time the app's been
            # started, then it's likely that the user's data file
            # has been moved somewhere else or has been deleted.
            # For the sake of graceful degradation we will need to
            # handle this scenario.
            print("\nPlease locate your .simplestash.yml and place it in your home folder.")
            print("If you cannot locate it, run 'python simplestash.py regenerate' which will make a new config for you.")
            print("Simplestash will exit now.")
            exit_app(1)
    else:
        # This would be the regular usage scenario
        # If the user does have the data file we can be pretty sure that
        # they don't need to do the first-time setup
        begin_log()
        log(f"Simplestash started normally with arguments '{' '.join(sys.argv[1:])}'")
        # Parse command line arguments
        parse_args(sys.argv)
        exit_app(0)
        # We still need to check that the yaml data is valid in case the user accidentally
        # edits it and breaks it

def exit_app(code: int):
    log("App closing")
    log(f"Log ended at {current_time()}")
    sys.exit(code)


def writeyaml(data_dict):
    with open(app_database_file, "w") as f:
        yaml.dump(data_dict, f)


def log(item):
    item = str(item) + "\n"
    with open(app_logfile, "a") as f:
        f.write(item)


def current_time():
    return datetime.now().strftime("%m/%d/%Y %H:%M:%S")


def begin_log():
    log(f"Starting log at {current_time()}")

def parse_args(args):
    # Read database into app database
    with open(app_database_file) as f:
        app_data = yaml.load(f, Loader=SafeLoader)
    num_of_args = len(args)
    if num_of_args <= 1:
        log("No arguments entered, help message shown instead.")
        # Show help message and exemplar usage
        help_handler("You seem to have forgotten to enter an argument! Check again that you've used at least 1 argument.")
    elif num_of_args > 2:
        print("More than one argument entered, help message shown instead")
        # Show help message and exemplar usage
        help_handler("Your arguments don't seem quite right! Check again that you've used the correct arguments.")
    else:
        validated_args = args[1:]
        first_arg = validated_args[0]
        if validated_args[0] in ["new", "help", "list", "cp", "reset", "viewlog"]:
            log(f"Received valid args '{' '.join(validated_args)}'")
            run_func(first_arg, app_data)
        else:
            help_handler(f"'{first_arg}' is not a valid argument, try again.")


def run_func(argument, subarg):
    # TODO: Make that switch statement work, it doesn't work rn!
    if argument == "new":
        input_new(subarg)
    elif argument == "help":
        help_handler()
    elif argument == "list":
        view_links(subarg)
    elif argument == "cp":
        cp_link(subarg)
    elif argument == "reset":
        temp(subarg)
    elif argument == "viewlog":
        temp(subarg)
    else:
        print("Invalid function, exiting.")
        log(f"Received invalid choice '{argument}' to run")
        exit_app(1)
    # log("Switcher received task {argument}")
    # Switch statement equivalent in Python
    # switcher = {
    #     "new": input_new(subarg),
    #     "help": help_handler(subarg),
    #     "list": view_links(subarg),
    #     "cp": temp(subarg),
    #     "reset": temp(subarg),
    #     "viewlog": temp(subarg)
    # }
    #print(f"Switcher received task '{argument}' with result \'{switcher.get(argument, 'Invalid function')}\'")
    # return switcher.get(argument, "Invalid function")


def temp(subarg):
    print("Sorry, this feature is not finished yet")
    exit_app(0)

def input_new(appdata_dict):
    print("Enter your new link below:")
    result = input("> ")
    log(f"Got raw user input '{result}'")
    # Parse the link syntax into the dict
    # The label is between the '#' and ':'
    # The link is between ':' and the end of the line
    label_regex = r"^\#.*?:"
    # Check if it matches, if not warn that the user did not follow the syntax
    while re.match(label_regex, result) is None:
        log(f"Invalid syntax for new input, aborted.")
        print("\nYou seem to have used the wrong input syntax.")
        print("The correct syntax is #Link Name:https://your-link-url\n")
        print("Enter your link below again:")
        result = input("> ")
    # We want to remove the # hashtag and : colon from the result
    # so we use slice it from index 1 to -1
    label = re.findall(label_regex, result)[0][1:-1]
    # Same here, we need to remove the # and : from the start
    # of the link so we slice it from index 2 onwards
    link = result.replace(label, "")[2:]
    log(f"Added label: {label}\nAdded link: {link}")
    # Add to dict now
    appdata_dict["links"][label] = link
    print(f"{check_symbol} Link added!")
    writeyaml(appdata_dict)
    exit_app(0)


def view_links(appdata_dict):
    # Title for links
    print("\n  Your Links\n  ----------\n")
    for label in appdata_dict["links"]:
        link = appdata_dict["links"][label]
        # Print a blank line after the last line
        # it looks better that way
        if label == list(appdata_dict["links"])[-1]:
            print(f" • {label} → {link}\n")
        else:
            print(f" • {label} → {link}")
    exit_app(0)


def cp_link(appdata_dict):
    print("Select the link you want to copy:")
    # Select the link with terminal ui selectmenu
    select_options = []
    for label in appdata_dict["links"]:
        select_options.append(label)
    terminal_menu = TerminalMenu(select_options)
    menu_entry_index = terminal_menu.show()
    # TODO: This link should be underlined via ANSI escape codes
    copied_link = appdata_dict["links"][select_options[menu_entry_index]]
    clipboard.copy(copied_link)
    print(f"{check_symbol} Copied link {Format.underline + copied_link + Format.end}!")


if __name__ == "__main__":
    read_config_file()
