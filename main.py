import subprocess
import queue
import threading
import plistlib
from rich import print
from rich import box
from rich.bar import Bar
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from datetime import datetime
from rich.live import Live
import os
import sys


def enqueue_output(pipe, queue):
    try:
        buffer = ''  # Initialize a buffer to hold incoming data
        while True:
            chunk = pipe.read(1024)  # Read in chunks
            if chunk:
                buffer += chunk  # Add the chunk to the buffer
                while '\0' in buffer:  # Check if there is a NUL character in the buffer
                    # Split the buffer at the first NUL character
                    message, buffer = buffer.split('\0', 1)
                    try:
                        # Parse the plist data
                        plist_data = plistlib.loads(message.encode('utf-8'))
                        # Put the parsed plist data in the queue
                        queue.put(plist_data)
                    except Exception as e:
                        print(f"Error parsing plist: {e}")
            else:
                # If no more data, put any remaining buffered data into the queue
                if buffer:
                    queue.put(buffer)
                break
    except Exception as e:
        print(f"Error reading output: {e}")
    finally:
        pipe.close()


def update_cpus(plist):
    processor_info = plist.get('processor', {})
    clusters = processor_info.get('clusters', [])
    if clusters:  # Check if clusters is not empty
        for cluster in clusters:
            for cpu in cluster["cpus"]:
                cpus[cluster["name"]+"_" +
                     str(cpu["cpu"])].end = 1-cpu["idle_ratio"]


def update_gpus(plist):
    gpu_info = plist.get('gpu', {})
    gpu.end = 1 - gpu_info.get("idle_ratio", 1)


def update_process(plist) -> Table:
    table = Table(expand=True)
    # table.add_column("id", justify="right", width=5)
    table.add_column("cpu_time", justify="right", ratio=1)
    table.add_column("gpu_time", justify="right", ratio=1)
    table.add_column("bytes_read", justify="right", ratio=1)
    table.add_column("bytes_written", justify="right", ratio=1)
    
    table.add_column("name", ratio=10)

    tasks = plist.get('coalitions', [])
    for task in tasks:
        table.add_row(*[str(task["cputime_ms_per_s"]), 
                        str(task.get("gputime_ms_per_s", 0)),
                        str(task.get("diskio_bytesread",0)), 
                        str(task.get("diskio_byteswritten",0)), 
                        task["name"]])

    return table


def make_layout(plist) -> Layout:
    processor_info = plist.get('processor', {})
    clusters = processor_info.get('clusters', [])
    """Define the layout."""
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3),
        Layout(name="cpus", size=5),
        Layout(name="gpu", size=3),
        Layout(name="process", ratio=1),
    )
    grid = Table.grid(expand=True)
    cluster_panels = []
    for cluster in clusters:
        cpu_panels = []
        grid.add_column(ratio=len(cluster["cpus"]))
        cpu_table = Table.grid()
        for cpu in cluster["cpus"]:
            b = Bar(1, begin=0, end=0)
            cpus[cluster["name"]+"_"+str(cpu["cpu"])] = b
            cpu_panels.append(Panel(b, box=box.SQUARE))
        cpu_table.add_row(*cpu_panels)
        cluster_panels.append(
            Panel(cpu_table, title=cluster["name"], box=box.SQUARE))
    grid.add_row(*cluster_panels)
    layout["cpus"].update(grid)
    gpu_grid = Table.grid(expand=True)
    gpu_grid.add_row(Panel(gpu, title="GPU", box=box.SQUARE))
    layout["gpu"].update(gpu_grid)

    return layout


class Header:
    """Display header with clock."""

    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            "[b]mxtop[/b] Apple Silicon",
            datetime.now().ctime().replace(":", "[blink]:[/]"),
        )
        return Panel(grid, style="white on blue", box=box.SQUARE)


# Globals
cpus = {}
gpu = Bar(1, begin=0, end=0)


def main():
    # Check if the current user ID is not 0 (root)
    if os.geteuid() != 0:
        sys.exit("This script must be run as root. Please use sudo.")
    output_queue = queue.LifoQueue()

    command = [
        'sudo', 'powermetrics',
        '--show-process-coalition',
        '--show-process-gpu',
        '--samplers', 'tasks,cpu_power,gpu_power,thermal',
        '-i', '1000',
        '-f', 'plist'
    ]

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    t = threading.Thread(target=enqueue_output,
                         args=(process.stdout, output_queue))
    t.daemon = True
    t.start()

    try:
        # Wait for the first plist item
        first_plist = output_queue.get(timeout=30)

        # Initialize the layout and components with the first plist
        layout = make_layout(first_plist)
        update_cpus(first_plist)
        update_gpus(first_plist)
        table = update_process(first_plist)

        layout["header"].update(Header())
        layout["process"].update(table)
        # Start the Live display
        with Live(layout, refresh_per_second=10, screen=True):
            while True:
                plist = output_queue.get(timeout=30)
                update_cpus(plist)
                update_gpus(plist)
                table = update_process(plist)
                layout["process"].update(table)
    except queue.Empty:
        print("No more items in queue.")
    except KeyboardInterrupt:
        print("Interrupted by user.")

    process.terminate()


if __name__ == '__main__':
    main()
