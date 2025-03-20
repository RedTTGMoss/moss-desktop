---
icon: books
description: >-
  This page explains the basics when starting to develop new extensions for
  moss!
---

# Getting started

## Choosing an SDK

Moss uses [Extism](https://extism.org/) for it's extensions, so you can use any PDK (plugin development kit) to make your Moss extension, but you would have to implement all or any of the Moss host functions you need to use!

Officially Moss will have continued implementations for the [rust extism pdk](https://github.com/extism/rust-pdk), you can find the extension template and setup instructions on the [extension\_rust\_template github](https://github.com/RedTTGMoss/extension_rust_template), other Moss SDKs by contributes include:

* .NET - [Moss.NET.SDK By furesoft](https://github.com/RedTTGMoss/Moss.NET.SDK)

You can also use other people's extensions if they are open sourced and properly licensed! Moss has some official extensions you can consider example code:

* [Dark Mode By RedTTG](https://github.com/RedTTGMoss/extension_dark_mode)

## Developing

This section will describe some basic things within Moss's extension system and all the quirks before you get started

### Preparing your extension

You can start by initializing a development environment for your extension.

#### Extension paths

Moss keeps all the extensions under the path `content/extensions/<Extension Name>` Additionally Moss will only accept the file inside `<Extension Name>.wasm` So your first step is to make your project in this folder and set up your building process to result in that file so Moss can find it!

#### Wasi

Moss also uses **wasi** so make sure your extension has that in its build configuration as well!

#### Enable the extension

Moss should now see your extension if you already built it. But upon running Moss you won't find it loading. This is a security measure and any foreign extensions that Moss hasn't installed itself are by default <mark style="color:red;">**disabled**</mark> so head over to your `config.json` and set it to `true` under `extensions > <Extension Name>` Finally Moss should now recognize and load your extension just fine!

### Required functions

Development is straightforward, Moss provides 3 functions which are considered entry points\
These are required and are:

`moss_extension_register(state: MossState) -> ExtensionInfo` - This is the initial entry point of your extension, called during the Moss loading process.

`moss_extension_loop(state: MossState)` - This function is called on every frame.

`moss_extension_unregister()` - This function is called upon closing Moss or unloading.

While these are all the functions Moss extension manager will call directly to maintain your extension and they are required, you may pass callbacks in some situations to trigger custom functions in your extension.

Anyway, you can find the host functions that _**your extension**_ can call in the next section [host-functions.md](host-functions.md "mention") If you find something missing, make sure to suggest it be added to the Moss extension SDK

## Publishing

### Consider open sourcing!

After making your extension, you can share your code to the [Moss github organization](https://github.com/RedTTGMoss) if you want, by asking one of the admins and transferring it there.

If you don't want to do that then you can still open source your code if you'd like, however Moss does not stop you from keeping it closed source, but we are less likely to be able to help if you're having issues interacting with the Moss extension SDK.

### The moss content store

Moss has a public store full of extensions! You can publish your extension there and get the benefit of easily allowing Moss content store users to download your extension through Moss!

Find out more at [moss.redttg.com](https://moss.redttg.com).

### Manual installation

You can share your `wasm` file or extension folder in a zip (since extensions may include assets) and allow the user to add it to their `content/extensions` folder and enable it manually!

Moss will create and move the `wasm` file into a same named folder if you just place it into the extensions directory, so you can skip that step for your users in case your extension doesn't bundle any assets.
