# MAI-BIAS modules

[![Integration Tests](https://github.com/mammoth-eu/mammoth-commons/actions/workflows/integration.yml/badge.svg)](https://github.com/mammoth-eu/mammoth-commons/actions/workflows/integration.yml)
![Coverage](./coverage-badge.svg)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md) 

*Quickly develop and locally run MAI-BIAS toolkit modules.*

This repository holds the mammoth-commons library with supporting
datatypes and decorators shared by various toolkit modules.
It also hosts a catalogue of dataset loaders, model loaders, and fairness analysis 
and mitigation modules. Finally, find ad desktop application that 
runs the modules in your local machine.

![logo](demonstrator/logo.png)

## 🔬 Run locally

*Depending on your operating system, replace `python` with `python3` below.*

1. Install Python 3.11 or later. Make **sure** the version is appropriate with `python --version`.
2. Download or clone this repository. Prefer working in a virtual environment.
3. Install dependencies with `pip install -r requirements[test].txt`. This can take a bit of time.
4. Launch the local app with `python demonstrator/app.py` or `python -m demonstrator.app`.

<details><summary>WSL missing .so files</summary>
    
If you are in WSL, you are likely to get errors like this *ImportError: libGL.so.1: cannot open shared object file: No such file or directory*.
This is due to the lack of a graphical environment. Install one like like below, including missing font symbols needed to properly display certain UI element.

```bash
sudo apt update
sudo apt install fonts-noto-color-emoji fonts-symbola
sudo apt install libgl1 libxkbcommon-x11-0 libegl1 libnss3 libxcomposite1 \
                 libxdamage1 libxrender1 libxrandr2 libxtst6 libxi6 libasound2 \
                 libxkbfile-dev qt6-wayland libxcb-cursor0 libx11-xcb1 libxcb-xinerama0
```

</details>

<details><summary>VSCode launch profile</summary>  

```json 
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false,
            "cwd": "${workspaceFolder}",
        },
        {
            "name": "Python: Test",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false,
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Demonstrator",
            "type": "debugpy",
            "request": "launch",
            "module": "demonstrator.app",
            "justMyCode": false
        }
    ]
}
``` 
</details>
 
## 🖥 [Deploy in a server](https://github.com/mammoth-eu/mammoth-toolkit-releases)

## :clipboard: [Module catalogue](https://mammoth-eu.github.io/mammoth-commons/)

## :thumbsup: [Contribute](CONTRIBUTING.md)
