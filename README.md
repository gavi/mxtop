# mxtop

## Overview
This script provides a real-time monitoring tool for system metrics, including CPU and GPU usage, as well as process information, specifically tailored for Apple Silicon Macs. It utilizes the `powermetrics` command for data collection and the `rich` library to display this information in a visually appealing console interface.

## Features
- Real-time CPU and GPU usage monitoring.
- Process information display.
- Visual layout using the `rich` console library.

## Requirements
- Python 3.x
- macOS with Apple Silicon.
- The `rich` Python library.

## Installation

### Clone the Repository
```bash
git clone [repository-url]
cd [repository-folder]
```

### Install Dependencies
```bash
pip install rich
```

## Usage

Run the script using Python:

```bash
sudo python3 main.py
```

Ensure you have the necessary permissions to execute the `powermetrics` command.

## Configuration

No additional configuration is required. The script is ready to run as is, assuming all dependencies are met.

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request for any enhancements, bug fixes, or improvements.

## License

This project is licensed under the MIT.

