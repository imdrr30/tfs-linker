import json
import subprocess
import os
import sys

TFS_LINKER_FOLDER = ".tfslinker"
WORKING_DIR = os.getcwd()
QUEUE_KEY = "queue"


class TFSConnectionFailed(Exception):
    pass


def get_queue_path():
    tfs_folder_path = os.path.join(WORKING_DIR, TFS_LINKER_FOLDER)
    os.makedirs(tfs_folder_path, exist_ok=True)
    return os.path.join(os.path.join(tfs_folder_path, "queue.json"))


def read_queue():
    if os.path.exists(get_queue_path()):
        try:
            with open(get_queue_path(), "r") as queue:
                return json.load(queue)[QUEUE_KEY]
        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            write_queue([])
            return read_queue()
    return []


def write_queue(files_queue):
    with open(get_queue_path(), "w") as queue:
        json.dump({QUEUE_KEY: files_queue}, queue)


def fake_modification(file_path):
    file_path = os.path.join(WORKING_DIR, file_path)
    modification_time = os.path.getmtime(file_path)
    os.utime(file_path, (modification_time + 0.1, modification_time + 0.1))


def execute_tfs(command):
    return subprocess.run([sys.argv[2], *command], capture_output=True, text=True)


def run_tfs_command(file_path):
    queue = read_queue()

    # Perform a comparison between the local file and the latest server version
    tf_diff_command = ["diff", "/version:T", file_path]
    tf_diff_output = execute_tfs(tf_diff_command)

    if tf_diff_output.returncode == 0:
        changed_lines = [
            line
            for line in tf_diff_output.stdout.split("\n")
            if line.startswith("+") or line.startswith("-")
        ]
        if changed_lines:
            print("There are changed lines:")
            tfs_checkout_command = ["checkout", file_path]
            execute_tfs(tfs_checkout_command)
        else:
            print("There are no changed lines.")
            tfs_undo_command = ["undo", file_path]
            execute_tfs(tfs_undo_command)

        if queue:
            for file in queue:
                fake_modification(file)

        write_queue([])

    else:
        print("File previously does not exist.")
        tfs_add_command = ["add", file_path]
        add_output = execute_tfs(tfs_add_command)

        if add_output.returncode == 100:
            print("Following files will be synced after connecting to internet.")
            if file_path not in queue:
                queue.append(file_path)
                write_queue(queue)
            print("\n".join(queue))
            raise TFSConnectionFailed("Can't connect to TFS.")


def run_linker():
    if len(sys.argv) > 2:
        file_path = sys.argv[1]
        run_tfs_command(file_path)
    else:
        print("No arguments provided.")
