# ACMOJ CLI  - Unofficial Command Line Interface for ACMOJ

## Table of contents

1. [Introduction](#introduction)
2. [Installation Guide for Ubuntu/WSL](#installation-guide-for-ubuntuwsl)
    - [Prerequisites](#prerequisites)
    - [Steps](#steps)
3. [Usage Guide](#usage-guide)
    - [Login](#login)
    - [Create a new file](#create-a-new-file)
    - [Submit a solution](#submit-a-solution)
    - [Track submission status](#track-submission-status)
    - [More help](#more-help)
4. [Customization Guide](#customization-guide)
    - [Change author](#change-author)
    - [Edit code templates](#edit-code-templates)

## Introduction
ACMOJ CLI is an unofficial command line interface utility designed to interact with the Shanghai Jiao Tong University (SJTU) [ACM Online Judge (ACMOJ)](https://acm.sjtu.edu.cn/OnlineJudge/). It provides an easy and convenient way to perform problem submissions and track submission statuses from the command line, without needing to open your browser. The tool also allows you to manage source file templates with standardized comment sections containing metadata about the problem and author.

The main features of `acmoj` include:
- Seamless problem submission to the ACMOJ platform.
- Automatic login using stored session cookies.
- Create new source files with predefined templates.
- Track submission status in real-time.
- View the status of previous submissions without logging into the website.

## Installation Guide for Ubuntu/WSL

Follow the steps below to get `acmoj` up and running on your terminal environment (Ubuntu/WSL):

### Prerequisites

Make sure the following dependencies are in place:

1. Python 3.x
2. `pip` (Python's package installer)

Install any missing dependencies via the following commands:

```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Steps

#### 1. Install `requests`

The tool relies on the popular Python library `requests` to interact with the ACMOJ platform. Install it using `pip`:

```bash
pip install requests
```

#### 2. Clone the `acmoj` repository

```bash
git clone https://github.com/stargazerZJ/ACMOJ-CLI.git ~/.config/acmoj
```

#### 3. Create a symlink to `.local/bin`

This step ensures that you can call the `acmoj` command from anywhere in your terminal.

```bash
mkdir -p ~/.local/bin
ln -s ~/.config/acmoj/acmoj.py ~/.local/bin/acmoj
chmod +x ~/.local/bin/acmoj
```

#### 4. Add `~/.local/bin` to the `PATH`

Ensure that your terminal environment knows where to find the `acmoj` command. Add the following line to your `~/.bashrc` (for bash users) or `~/.zshrc` (for zsh users):

```bash
export PATH=$PATH:~/.local/bin
```

After editing the shell configuration file (`~/.bashrc` or `~/.zshrc`), apply the changes:

```bash
source ~/.bashrc   # for bash users
# OR
source ~/.zshrc    # for zsh users
```

#### 5. Verify the installation

To check if the installation was successful, run:

```bash
acmoj -h
```

If the installation was successful, you should see the help message for the `acmoj` command.

Congratulations! You've successfully installed `acmoj` on your system. 🎉

## Usage Guide

The tool provides several CLI subcommands, mostly tied to typical workflows like logging in, submitting code, and tracking submissions.

Open the terminal and call `acmoj` with these various commands:

### Login

You need to log in before making submissions.

```bash
acmoj login -u <your_username>
```

- You will be prompted to enter your `password`.
- This stores a login cookie locally, meaning you won't have to log in every time.

### Create a new file

To quickly generate a new source file for a problem:

```bash
acmoj new <problem_id>
```

- The command creates a new `.cpp` file with metadata (such as `Problem ID`, `Date`, `Author`).
- Optionally, you can specify an algorithm tag with the flag `-a` to categorize your solution better.

Example:

```bash
acmoj new 12345 -a "Dynamic Programming"
```

### Submit a solution

Submit your solution by specifying the file path and problem ID.

```bash
acmoj submit <source_path> -p <problem_id>
```

- You can omit `-p problem_id` if the problem ID is already present within the source file's pre-filled comments.
- To track your submission status in real time, use the flag `-t`:

```bash
acmoj submit <source_path> -p <problem_id> -t
```

### Track submission status

To check the status of the most recent submission:

```bash
acmoj status
```

Provide the submission ID explicitly if you want to see a past submission's status:

```bash
acmoj status <submission_id>
```

### More help

For more information on the available commands and their usage, run:

```bash
acmoj -h
```

To get help on a specific command, use:

```bash
acmoj <command> -h
```

Example:

```bash
acmoj submit -h
```

## Customization Guide

You can personalize the tool to suit your preferences by editing certain relevant parts like the author name or the code templates.

### Change author

Author information is included in the source file's metadata. By default, the author name is set to `You (your_email@sjtu.edu.cn)`.

To change the author globally, you can set the environment variable in your `.bashrc` or `.zshrc` file:

Edit your `.bashrc` or `.zshrc` file (for bash and zsh users respectively):

```bash
nano ~/.bashrc     # If you use Bash
nano ~/.zshrc      # If you use ZSH
```

Add the following line at the end:

```bash
export ACMOJ_AUTHOR="Your Name (your_email@sjtu.edu.cn)"
```

Then, reload your shell configuration:

```bash
source ~/.bashrc    # Bash
source ~/.zshrc     # ZSH
```

### Edit code templates

The templates help you ensure a consistent structure for all of your submissions.

The template is stored at:

```bash
~/.config/acmoj/template.cpp
```

You can customize the template file to fit your own coding style:

```bash
nano ~/.config/acmoj/template.cpp
```

For example, a simple `template.cpp` could look like this:

```cpp
#include<bits/stdc++.h>
using namespace std;

int main() {
    cout << "Hello World!" << endl;
    return 0;
}
```

This will be automatically filled into the new problem file whenever you run `acmoj new`.

---

Now you're ready to start using ACMOJ CLI! If you have any issues or suggestions, feel free to open an issue on the GitHub repository. Happy coding and good luck with your competitions! 🎉