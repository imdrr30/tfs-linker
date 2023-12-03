import os
from pathlib import Path

PACKAGE_PATH = Path(os.path.abspath(__file__)).parent.resolve()


def get_input(message, default, failed=False):

    message_string = "Try again: " if failed else message + ": "
    value = input(message_string) or default
    return value if value else get_input(message, default, failed=True)


def auto_detect_workspace(cwd):
    search_for = r"\Dev"
    if search_for in cwd:
        index = cwd.find(search_for)
        return cwd[:index + len(search_for)]
    return None


def configure_idea():
    current_working_directory = os.getcwd()
    print("current working dir: " + current_working_directory)
    idea_folder = os.path.join(current_working_directory, ".idea")
    os.makedirs(idea_folder, exist_ok=True)

    watchers_path = os.path.join(idea_folder, "watcherTasks.xml")

    start_setup = True

    if os.path.exists(watchers_path):
        confirmation = input("watchers Configuration already exists. Override with new one ? (y/n) (default:n): ") or "n"
        start_setup = confirmation == "y"

    tfs_exe = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\TF.exe"

    if start_setup:
        xml_config = open(os.path.join(PACKAGE_PATH, "watchersConfig.xml"), "r").read()

        config_to_get = {
            "workspaceDirectory": {
                "description": "TFS Working directory absolute path.\n\teg. D:/Projects/Workspace/Dev",
                "default": auto_detect_workspace(current_working_directory)
            },
            "tfsExecutablePath": {
                "description": "Path to TFS executable binary",
                "default": tfs_exe
            }
        }

        configs_retrieved = {}

        for config_name, info in config_to_get.items():
            description_message = info.get("description")
            default = info.get("default")
            if default:
                description_message += f"\n(default: {default})"
            configs_retrieved[config_name] = get_input(description_message, default)

        relative_path = os.path.relpath(os.getcwd(), configs_retrieved["workspaceDirectory"])

        configs_retrieved["workingDirectory"] = relative_path

        for key, value in configs_retrieved.items():
            xml_config = xml_config.replace("{{"+key+"}}", value)

        with open(watchers_path, "w") as config_file:
            config_file.write(xml_config)

        print("Configuration added.")
