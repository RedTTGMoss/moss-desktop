# Moss desktop app

An app for working with your documents in the reMarkable cloud

[![using](https://img.shields.io/badge/using-Extism-4c30fc.svg?subject=using&status=Extism&color=4c30fc)](https://extism.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/RedTTGMoss/moss-desktop/total)
![GitHub Repo stars](https://img.shields.io/github/stars/RedTTGMoss/moss-desktop)
[![wakatime](https://wakatime.com/badge/github/RedTTGMoss/moss-desktop.svg)](https://wakatime.com/badge/github/RedTTGMoss/moss-desktop)

### [Docs](https://redttg.gitbook.io/moss/)

This project is entirely open source.
If you encounter any issues, you can use the GitHub issues to let the contributors know!

An open-source app for working with your documents in the reMarkable cloud

## Installation & Portable mode

You'll find builds under releases. The executable contains the app and an installer.

## Usage notes

Using this app to access your reMarkable cloud
may cause reMarkable to take action on your account.
So use this app at your own discretion!

The app supports the api completely!

For information on how you can use moss check out the [docs](https://redttg.gitbook.io/moss/)

## Extensions

Moss uses [extism](https://extism.org/) to support user extensions.

There are several examples available:

[.Net](https://github.com/RedTTGMoss/Moss.NET.SDK)

[Dark mode with Rust](https://github.com/RedTTGMoss/extension_dark_mode)

[Rust Sdk Tester](https://github.com/RedTTGMoss/rust_sdk_tester)

[Moonbit](https://github.com/furesoft/moos-sdk-tester)

A brief instruction how to write your own extensions in the language of your choice can be found at
the [docs](https://redttg.gitbook.io/moss/extensions/getting-started).

Here are some planned extensions We will create!

- Replace PDF function (the origin of this whole project)
- PDF Templates Store (with update support) **PLANNED NATIVE SUPPORT**
- nyaa.si ebook/pdf download
- Image(s) to PDF import
- Add Image to PDF function (from suggestion)
- Content Store (A hub of verified extensions and notebooks)
- Archiving (Automatically move documents to collection based on certain conditions like a tag or date)
- Aggregated rss news feed
- Wikipedia crawler

## Contribution

This section describes the steps for contributors on how to prepare their work environment

**Moss is tested with python 3.9 (but this is no longer a must)**

*If you want to use your own cloud set it first in the config or in the gui*

1. Fork this repository and clone it with submodules like `git clone --recursive `
2. Setup a virtual environment or use the global one, with minimum python version `3.9`
3. Install the dependencies requirements.txt, rm_lines/requirements.txt, rm_api/requirements.txt
4. Install system dependant requirements, from
   requirements-Linux.txt, requirements-Windows.txt or requirements-macOS.txt respectively
5. Run the moss.py file
6. Set up your cloud connection
7. Wait for the initial sync
8. Please note that if you are developing changes to the cache system, all cached files are stored in sync folder
9. Make changes and test a new feature
   The look and feel of this feature has to be paper-like
10. Make your pull request.

- Use the config.json or settings, you can set `debug` *+ more* to `true` in there!

A few things will be checked

- Different screen resolution support
- API compatibility
- etc.