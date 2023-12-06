import os
from pathlib import Path
import subprocess
import re
from .exceptions import TFSWorkSpaceNotFound, InvalidIntelliJIDEProjectPath

PACKAGE_PATH = Path(os.path.abspath(__file__)).parent.resolve()


def execute_tfs(command):
    return subprocess.run(command, capture_output=True, text=True)


def get_input(message, default=None, failed=False):
    message_string = "Try again: " if failed else message + ": "
    value = input(message_string) or default
    return value if value else get_input(message, default, failed=True)


def auto_detect_workspace(cwd):
    search_for = r"\Source"
    if search_for in cwd:
        index = cwd.find(search_for)
        return cwd[: index + len(search_for)]
    return None


def validate_tfs_executable(exe_path):
    validate_output = execute_tfs([exe_path])
    if "Microsoft (R) TF - Team Foundation Version Control Tool" in validate_output.stdout:
        return exe_path
    else:
        return validate_tfs_executable(get_input("TFS exe not found, please provide it: "))


def find_common_path(server_path, local_path):
    server_path_list = server_path.split("/")
    local_path_list = local_path.split("\\")

    index = 0

    for i in range(len(local_path_list)):
        index = -(i + 1)
        if local_path_list[index] != server_path_list[index]:
            break

    if not index:
        raise TFSWorkSpaceNotFound("Could not map the TFS path.")

    return "\\".join(local_path_list[:index+1])


def current_directory_for_tfs_validate_tfs_directory(tfs_exe):
    info_command = execute_tfs([tfs_exe, "info", "."])

    output = info_command.stdout
    local_path_pattern = re.compile(r'Local path\s*:\s*(.*)', re.IGNORECASE)
    server_path_pattern = re.compile(r'Server path\s*:\s*(.*)', re.IGNORECASE)
    local_path_match = local_path_pattern.search(output)
    server_path_match = server_path_pattern.search(output)

    if not local_path_match or not server_path_match:
        raise TFSWorkSpaceNotFound("TFS Workspace not found in the current working directory.")

    local_path = local_path_match.group(1).strip()
    server_path = server_path_match.group(1).strip()

    return find_common_path(server_path=server_path, local_path=local_path)


def configure_idea():
    current_working_directory = os.getcwd()
    idea_folder = os.path.join(current_working_directory, ".idea")
    if not os.path.exists(idea_folder):
        raise InvalidIntelliJIDEProjectPath("Not an valid IDEA IDE Project.")

    os.makedirs(idea_folder, exist_ok=True)

    watchers_path = os.path.join(idea_folder, "watcherTasks.xml")

    start_setup = True

    if os.path.exists(watchers_path):
        confirmation = (
            input(
                "watchers Configuration already exists. Override with new one ? (y/n) (default:n): "
            )
            or "n"
        )
        start_setup = confirmation == "y"

    default_tfs_exe = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\TF.exe"

    if start_setup:
        xml_config = open(os.path.join(PACKAGE_PATH, "watchersConfig.xml"), "r").read()

        configs_retrieved = {}

        tfs_exe = validate_tfs_executable(default_tfs_exe)

        print("Valid TFS executable found at: " + tfs_exe)

        configs_retrieved["tfsExecutablePath"] = tfs_exe

        workspace_directory = current_directory_for_tfs_validate_tfs_directory(tfs_exe)

        configs_retrieved["workspaceDirectory"] = workspace_directory

        print("Valid TFS directory found at: " + workspace_directory)

        relative_path = os.path.relpath(
            current_working_directory, configs_retrieved["workspaceDirectory"]
        )

        print("Relative path from the TFS Directory: " + relative_path)

        configs_retrieved["workingDirectory"] = relative_path

        for key, value in configs_retrieved.items():
            xml_config = xml_config.replace("{{" + key + "}}", value)

        with open(watchers_path, "w") as config_file:
            config_file.write(xml_config)

        print("Verify the added configuration at File->Settings->Tools->File Watchers, Look for TFS Linker.")
        print("Name: TFS Linker")
        print("Files to Watch:")

        print("\t\tFile Type: Any")
        print("\t\tScope: Project Files")

        print("Tool to Run on Changes:")
        print("\t\tProgram: tfs-linker")
        print(f'\t\tArguments: "{relative_path}\$FilePathRelativeToProjectRoot$" "{tfs_exe}"')
        print('\t\tOutput paths to refresh: (leave empty)')
        print(f'\t\tWorking directory: {workspace_directory}')
        print('\t\tEnvironment variables: (leave empty)')
        print("Advanced Options:")

        print("\t\tAuto-save edited files to trigger the watcher: enabled")
        print("\t\tTrigger the watcher on external changes: enabled")
        print("\t\tTrigger the watcher regardless of syntax errors: enabled")
        print("\t\tCreate output file from stdout: disabled")
        print("\t\tShow console: On error")
        print("\t\tOutput filters: (leave empty)")
        print("Click on Ok to save.")
        print("Configuration added Successfully.")
        print("Verify the added configuration at File->Settings->Tools->File Watchers, Look for TFS Linker.")
        print("Added it manually in case if you can not find the TFS Linker following the above steps.")

