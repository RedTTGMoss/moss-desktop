---
icon: code-pull-request
description: Everything you need to get Moss running from source
---

# Development and contribution

## Environment

This will include everything that is needed to run Moss or build it too

### Setting up python 3.9

Prepare your python environment, you want to get python version 3.9 installed on your system.\
I cannot provide instructions for every operating system but generally you can find how to get python running on the python website

> If you are on linux you might want to also install `python3.9-tk`

### Installing packages

There are a few things to install, these are the platform independent packages\
You can install them by doing `pip install -r requirements.txt`\
\
Furthermore install the platform specific packages, these are as follows

#### Windows

`pip install -r requirements-Windows.txt`

#### Linux

`pip install -r requirements-Linux.txt`

#### MacOS

`pip install -r requirements-macOS.txt`

> If you plan to build Moss to an executable binary, also prepare the `nuitka` package too\
> `pip install nuitka`

## Running Moss from the source code

After preparing you python environment it's time to check if Moss runs without any issues.\
You can run moss with `python moss.py` it should start without issues, if you get any issues report them to get added here, and look them up if you want

### Development warning messages

Moss will bring up a few messages to warn you if it detects that it's code is nearby.\
One of these will become quickly obviously if you pulled newer changes, particularly if `pygameextra` is noticed to have been bumped in the requirements file, you will see a warning to update it.

<figure><img src=".gitbook/assets/image (3).png" alt=""><figcaption><p>Moss complaining about pygameextra</p></figcaption></figure>

Another thing that Moss will tell you is that you've made changes!

<figure><img src=".gitbook/assets/image (1).png" alt=""><figcaption><p>Moss complaining that you haven't shared your changes</p></figcaption></figure>

As it states this message will only occur if you disable debug, it is meant to encourage you to push the changes you've made and not keep them for yourself, because if you've disabled debug mode it's expected you are either testing Moss or are using it casually from source.\
If you so desire you can remove this check and not push the commits.

## Using the Moss debug mode

By enabling debug mode in the config file for Moss, you can toggle a few things, you can also define your own checks for debug mode by simply checking if it is turned on.

### Debug button rects

You may have also noticed the `debug_button_rects` option in the config, this is a separated debug option because it messes with the visuals quite a bit and may lead to UI mistakes, but it can also help with button issues, if you find that a button isn't working or something is being blocked, this option will attempt to outline all the buttons using `pygameextra`'s build-in context last buttons

<figure><img src=".gitbook/assets/screenshot (2).png" alt="" width="506"><figcaption><p>Moss button rect debug</p></figcaption></figure>

As you can this mode isn't necessarily pleasing but if your buttons are missing the red outline can allow you to see it showing up somewhere else and it may help you figure out what's going on.&#x20;

You can test if the red box matches your button if your button has a hover color and the red outline triggers it then it means that's the thing that is wrong with your button.\\

Please also keep in mind that all buttons are layered automatically and handled by `pygameextra`'s contexting system. If your button isn't working it may be that another button is on top of it, so make sure to properly order your buttons and place them properly with everything else.

\
This is also useful for parts of the ui you don't really want to be pass-through, so for example the side bar above has a hidden button on the back to stop any clicks from reaching the documents.

## Scaling and ratios

Moss typically scales itself through a few steps

1. Moss will use the remarkable ratio for its initial screen size, it is 0.75:1 and it uses the scale found inside the config file with a base height of `1000` , however the user can resize the Moss window at any time!
2. The `aspect_ratio` file, this file contains all the sizes for every text, button, icon, menu and everything in-between, it automatically ensures that everything looks the same, no matter what scale you set it to

<div><figure><img src=".gitbook/assets/screenshot (3).png" alt=""><figcaption><p>Moss at 0.1 scale</p></figcaption></figure> <figure><img src=".gitbook/assets/screenshot (4).png" alt=""><figcaption><p>Moss at 0.3 scale</p></figcaption></figure></div>

### Detecting resize

Since the user can change the screen size at any time and some things rely on being centered or at the bottom of the screen, some things need to be _re-calibrated_ to the new size.\
The top-most context of Moss handles the event for this, if it detects a change in resolution it will spread a `ResizeEvent` through the api object, which will happily transmit these custom events, you can subscribe to receive the api events by doing something like this:\
`self.api.add_hook(f'my_class<{id(self)}>_resize', self.resize_check_hook)`

Of course, you can hook other api events or custom events, but most classes call it a resize\_hook since all they check is the resize event\
Please note that if your class or screen can have multiple instances it's a good idea to add the object id in the name, also save this since it identifies your hook.\
If your screen is closed or the object is no longer in use, it would be nice to remove your hook from the api, you can do so like this:\
`self.api.remove_hook(self.my_hook_name)`

Back to the resize event itself, it actually contains the new screen size, so you can use that directly or just call any functions that would have initially done the math anyway, but if you need, the event has a `new_size` variable you can use.

## The API

The Moss api object handles everything, including maintaining a list of all the documents and document\_collections, it also handles new and old api systems and managing document changes. So you can freely look though all the functions it includes, the main ones you'd be using are `upload` and `upload_many_documents` which are interchangeable except one takes a single item, the other takes a list, the same is true for `delete` and `delete_many_documents` which instead of taking care of changes will handle erasing the document or collection from the root file.

### How the API works

Here's a little in-depth explanation into the api or more over, how your documents are stored

#### The importance of the root file

The very top of your cloud is the root file, you'll see this mentioned here and there and it's one of the most important files, because it registers every single document and collection! What's worse is you can erase this file by telling the api that you want to use a nonexistent file as your root, typically Moss and the api object handle this, by cancelling the operation if they see anything wrong, if this happens Moss will crash before damaging the root file, but if it does then it will recreate it upon connecting and seeing this mishap.

However now all your files are gone! Moss has a dirty way of fixing this by pretty much restoring from it's own memory. Run `root_fixer.py` it will look through and find all previous root files that Moss synced and saved, it'll sort them for you by last modified and you can pick whichever one you think is accurate.

If you loose any data **PLEASE CONTACT REMARKABLE IMMEDIATELY!!**

#### The root file

The root file contains all your documents, but how? Well it's basically a massive list!\
But these items are more like pointers to individual lists for each item which actually has some more valuable information on the item.

#### The document files

If we look into one of the items in the root file and actually fetch that item it brings us into another list, but this time we can actually see identifiable files and even their extensions, this helps Moss and your tablet identify the files' data, there are a few main files that Moss must fetch, <mark style="color:yellow;">**the rest can be fetched later and they are usually the pdf, epub, rm files that actually contain the document data**</mark>, but what about your document information?

1. The metadata file - This file is very basic and contains the very important data, which would be mainly needed by the main menu, like the name, modification time and other small things
2. The content file - This file is much more complex and contains all the data, which the document renderer would need to be able to serve the document. Things like the document type, the template and index for each page, the tags, your last used pens, custom zoom levels and other minor things.

The api object in moss handles parsing this data for you and it also handles updating it, creating it and modifying it while maintaining full stability to the remarkable cloud and your tablet. This is especially true for [light sync](getting-started/moss-user-interface.md#light-sync), because if Moss didn't provide your tablet with the perfect data, the tablet would instantly try to correct it, which would result in the preview image messing up on the archived documents.
