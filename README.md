<p align="center">
<img src="https://i.imgur.com/9Z2Nnrf.png" width="500px" />
<br>
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/106185"><img src="https://i.imgur.com/STsBXT6.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="https://i.imgur.com/KcPrhK5.png" height="60px"/> </a>
<br>

# Description

This is an AI-based automatic Language Detector made to scan entire mod instances. It is used to find untranslated mods.
You will be able to scan through your entire mod list and see if there are any leftover mods that are in the wrong language. This will be particularly useful for translators and players who do not play their game with an English text version.
This is done using the the open source library called Lingua which uses NLP machine learning. However, this fully automated process might not always be 100% accurate. 
In order to achieve a more accurate end result in the long term, there is a dictionary function that can be used to add individual strings to a global whitelist. In this way, the selected string is declared in the language used by the user despite incorrect recognition. In most cases, however, it is sufficient to see that a certain percentage is defined as "not translated" in a plugin.

# Usage
- Extract the downloaded archive somewhere on your PC
- Add the "SSE-LD.exe" as tool in your favored mod manager (Do not use NMM)
- Setup your desired language on the top
- Skyrim Data-folder and path to loadorder.txt should be detected automatically.
- Hit the "Run"-button

You will be able to take a closer look at the found strings by right-clicking a plugin and hitting "Open string preview" or by double clicking on the "Untranslated Strings" column.
In the String Preview Dialog you are able to add strings or EDIDs (Editor IDs) to "dictionary" which is practically an ignore-list by right-clicking on them. 

# Features

- Fully automatic scan
- Bethesda Plugins (ESM, ESP, ESL)
- MCM files (TXT)
- Bethesda Archives (BSA)
- (Highly experimental!) Script files (PEX)

# Contributing

## 1. Feedback (Suggestions/Issues)

If you encountered an issue/error or you have a suggestion, create an issue under the "Issues" tab above.

## 2. Code contributions

1. Install Python 3.11 (Make sure that you add it to PATH!)
2. Clone repository
3. Open terminal in repository folder
4. Type in following command to install all requirements (Using a virtual environment is strongly recommended!):
   `pip install -r requirements.txt`

### 3. Execute from source

1. Open terminal in src folder
2. Execute main file
   `python main.py`

### 4. Compile and build executable

1. Follow the steps on this page [Nuitka.net](https://nuitka.net/doc/user-manual.html#usage) to install a C Compiler
2. Run `build.bat` with activated virtual environment from the root folder of this repo.
3. The executable and all dependencies are built in the main.dist-Folder.

## 3. Dictionary Sharing
You are free to share your personal Dictionary found in the executable's folder ("\SSE-LD\assets\dictionary.json")  as soon as you add something to it.

# Credits

- Qt by [The Qt Company Ltd](https://qt.io)
- [lingua-py](https://github.com/pemistahl/lingua-py) by [Peter M. Stahl](https://github.com/pemistahl)
- [Champollion PEX Decompiler](https://github.com/Orvid/Champollion) by [Orvid](https://github.com/Orvid)
- [McGuffin](https://www.nexusmods.com/starfield/users/3408338), Creator of [xTranslator](https://www.nexusmods.com/starfield/mods/313) who helped at filtering PEX-Files a bit better
- Icon by [Wuerfelhusten](https://nexusmods.com/users/122160268)
