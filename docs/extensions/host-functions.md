---
icon: link
description: >-
  This page details each host function and what it does. Each different module
  and group of functions are separated into their own section so you can quickly
  find what you need.
---

# Host functions

## In-Depth starter info

I recommend you read these first few sections before getting started.

### Global Types

```
Color:
- r: int - Red
- g: int - Green
- b: int - Blue
- a: Optional[int] - An optional alpha, default to 255 if not passed
```

```
TextColors:
- foreground: Color - The text color
- background: Optional[Color] - An optional background to put behind the text, to help with visibility
```

```
ConfigGet[T]: - Make sure you parse the value correctly once you receive it
- value: T - The typed return value 
```

```
ConfigSet[T]: - Make sure you serialize the value correctly when sending it
- key: str - The key of the particular item to be set
- value: T - The typed value to set
```

```
MossState:
- width: int - The width and of the moss window
- height: int
- current_screen: str - The class name of the current moss screen
- opened_context_menus: List[str] - A list of class names of all opened context menus
- icons: List[str] - A list of all the icons loaded by moss
```

```
ExtensionInfo:
- files: List[str] - A list of extension safe paths to load.
These can be any type as long as Moss loader supports loading them.
You would usually pass any custom icons as files.
```

{% hint style="success" %}
Moss will not start loading extensions until all assets are loaded
{% endhint %}

{% hint style="warning" %}
Moss will only load extension specified assets after all extensions are loaded
{% endhint %}

### Safe paths

Your extension will most of the time only be allowed several types. Moss will check these to ensure security. You can also access these paths in your extension where the filesystem access is handled by extism and not Moss.

```
temp - Links to Defaults.TEMP_DIR
extension - Dynamically links to your extension folder
options - Links to Defaults.OPTIONS_DIR
sync - Links to Defaults.SYNC_FILE_PATH
thumbnails - Links to Defaults.THUMB_FILE_PATH
assets - Links to Defaults.ASSET_DIR
```

For example if I had an asset in my extension folder `assets/ico.svg` I could simply refer to it as `extension/assets/ico.svg`&#x20;

Or if you wanted to do some manual evaluation of the cached sync files you could do something like `sync/{hash}` and so on...

### Default configuration and assets

Your extension is typically in `.wasm` format, but moss will automatically provide a folder for your extension. Moss will also accept `.zip` files too and even ask the user if they want to enable it.

Your extension can provide a default config to the Moss extension manager by having a **valid** `options.json` file in its associated folder.

### Registering your extension

Moss has 3 main functions that **must** be defined. These functions are your entrypoints.

```python
moss_extension_register(state: MossState) -> ExtensionInfo
```

<mark style="color:purple;">This function will be initially called by Moss when</mark> <mark style="color:purple;"></mark><mark style="color:purple;">**loading**</mark> <mark style="color:purple;"></mark><mark style="color:purple;">your extension</mark>. Its job is to define any extension wide values, prepare config, change defaults, register context menus and so forth. You are also required to return your extension information.

```python
moss_extension_loop(state: MossState)
```

This function is called once every frame. <mark style="color:yellow;">Please note that this function will</mark> <mark style="color:yellow;"></mark><mark style="color:yellow;">**not be called**</mark> <mark style="color:yellow;"></mark><mark style="color:yellow;">until the</mark> <mark style="color:yellow;"></mark><mark style="color:yellow;">**loading**</mark> <mark style="color:yellow;"></mark><mark style="color:yellow;">of Moss</mark> <mark style="color:yellow;"></mark><mark style="color:yellow;">**is completed!**</mark>

```python
moss_extension_unregister()
```

This function serves as a last chance for your extension to clean up any files or do any last minute configuration updates. <mark style="color:green;">This function gets called during</mark> <mark style="color:green;"></mark><mark style="color:green;">**reloads**</mark> <mark style="color:green;"></mark><mark style="color:green;">and when</mark> <mark style="color:green;"></mark><mark style="color:green;">**closing**</mark> <mark style="color:green;"></mark><mark style="color:green;">Moss.</mark>

## GUI functions

### GUI types

```markup
ContextButton:
- text: str - The text on the button
- icon: str - The icon to use for the button
- context_icon: Optional[str] - The bottom right icon used if your button is right clickable
- action: str - The extension function / callback to call when clicked
- context_menu: Optional[str] - The extension function to call to get the context menu when right clicked
```

```markup
ContextMenu:
- key: str - The key of your context menu
- buttons: List[ContextButton] - The buttons it should contain 
```

### Context menu functions

<pre class="language-python"><code class="lang-python"><strong>moss_gui_register_context_menu(menu: ContextMenu)
</strong></code></pre>

Creates a context menu within Moss that you can refer to. This function is usually meant to be called during extension registration.

```python
moss_gui_open_context_menu(key: str, x: int, y: int)
```

Activates any registered context menu onto your screen on the specified `x`and `y` coordinates. The context menu will remain open unless the user clicks outside of it.

### Miscellaneous functions

```python
moss_gui_invert_icon(key: str, result_key: str)
```

This function inverts any icon key you give it and will store the result into the respective result\_key. You can pass the same key both arguments to permanently invert that icon instead of making an inverted duplicate. You can use this to invert your own assets or to create something like the Moss dark mode extension.

## Defaults functions

Defaults refers to a class in Moss which globally describes every single configuration such as paths to folders or colors, these can be changed or viewed by extensions but whether or not Moss would respond to any changes depends highly on when you call any set function, it is recommended to do so at the registration stage!

### Functions for setting/getting colors

```python
moss_defaults_set_color(key: str, color: Color)
```

This function sets that particular color in the Defaults, ideal at registration.

```python
moss_defaults_get_color(key: str) -> Color
```

Likewise this function will return any particular color from the Defaults.

```python
moss_defaults_set_text_color(key: str, colors: TextColors)
```

This function sets that particular set of text colors in the Defaults, again ideal at registration, even though most UI will refresh texts depending on the situation.

```python
moss_defaults_get_text_color(key: str) -> TextColors
```

This function returns that particular set of text colors from the Defaults.

### Functions for setting/getting values

```python
moss_defaults_get(key: str) -> ConfigGet[T]
```

This function returns any value given the key in Defaults, it is passed to the extension as an object containing the typed value, your extension needs to properly parse the value's type.

```python
_moss_defaults_set(value: ConfigSet[T])
```

This function sets any value given the key in Defaults, it accepts the value as is from the extension and your extension needs to properly type it if it is updating an existing value. Your [SDK](getting-started.md#choosing-an-sdk) should abstract any type to be passed directly instead of `ConfigSet` .

## Extension manager functions (EM)

All these functions are closely related to either your interactions with Moss and the extension manager or accessing things available to your extensions / other extensions.

### Functions for setting/getting config values

Some of these are very similar to the defaults as they are related to setting the config file. You can take a look [above](host-functions.md#functions-for-setting-getting-values) for more information on these functions. Your extension is granted one config file it can use and it is automatically saved and managed for you.

```python
moss_em_config_get(key: str) -> ConfigGet[T]
```

<pre class="language-python"><code class="lang-python"><strong>_moss_em_config_set(value: ConfigSet[T])
</strong></code></pre>

### Functions for managing your extension

You can find more info on ContextButton [above](host-functions.md#types)

```python
moss_em_register_extension_button(button: ContextButton)
```

This function registers one or more context buttons to be passed to the side menu "Extensions" context menu. It is recommended that if you choose to add a button you'd only add one and then that would open a context menu or a screen that can there allow the user to further interact with your extension.

### Functions of the extension manager

```python
moss_em_export_statistical_data()
```

This function exports the extension manager's statistical call data to `TEMP_DIR/extension_calls.json` , the data is stored in the following format:

`dictionary -> extension_name : dictionary -> function_name : call count`&#x20;

{% hint style="warning" %}
Statistics have to be enabled by the user for Moss to setup the proper statistic tools
{% endhint %}

```python
moss_em_get_state() -> MossState
```

This function is useful if you need the state of Moss but are running code outside the loop function which would otherwise receive the state automatically.

## Pygame extra functions (PE)

### Pygame extra types

```
PygameExtraRectEdgeRounding:
- edge_rounding: Optional[int] - Sets all the below, -1 / None for disable
- edge_rounding_topright: Optional[int]
- edge_rounding_topleft: Optional[int]
- edge_rounding_bottomright: Optional[int]
- edge_rounding_bottomleft: Optional[int]
```

```
Rect:
- x: int - The left of the rect
- y: int - The top of the rect
- width: int - The width of the rect
- height: int - The height of the rect
```

```
PygameExtraRect:
- color: Color - The color of the rect
- rect: Rect - The rect of the rect lol
- width: int - The width of the rect's outline, or 0 for filled
- edge_rounding: Optional[PygameExtraRectEdgeRounding] - Optional rounding of the
```

```
Screen & ChildScreen: - These are considered UI rendering objects and will have respective context handling
- key: str - An identifier for the screen
- screen_pre_loop: Optional[str] - An extension function for the before loop call
- screen_loop: str - An extension function for the loop call
- screen_post_loop: Optional[str] - An extension function for the after loop call
- event_hook: Optional[str] - An extension function which will receive API events, must accept a single argument name: String
```

{% hint style="info" %}
Notice that everything except the key and loop are optional functions you can use and are not required to be passed!
{% endhint %}

### Functions for drawing basic shapes

```python
_moss_pe_draw_rect(draw: PygameExtraRect)
```

This function draws a basic rectangle. Your [SDK](getting-started.md#choosing-an-sdk) should abstract this, typically to expand the individual components of `PygameExtraRect` into arguments instead.

### Custom screens

The first steps for making custom screens with Moss is registering your extension's functions with a custom screen, so Moss can create your screen and call your extension

```python
moss_pe_register_screen(screen: Screen)
```

This function will register your screen with Moss, you can also use to register children screens, which are screens to be rendered on top of other screens (things like popups, context menus for example, but Moss already has those for you)

```python
_moss_pe_open_screen(key: str, initial_values: dict) -> int
```

This function will open a new instance of your screen in Moss. Your [SDK](getting-started.md#choosing-an-sdk) should manage the initial\_values to be serialized before passing through extism. It returns the id of the screen in Moss.

```python
moss_pe_get_screen_value(key: str) -> ConfigGet[T]
```

This function will get any value from the screen that you passed through using initial\_values or set separately. This function can optionally fetch variables or properties on the screen, as long as they are serializable.

```python
_moss_pe_set_screen_value(value: ConfigSet[T])
```

This function will update any value from the screen that you passed through using initial\_values or set any extra values.

## Text

Moss has an approach to text where you can create a text and Moss returns an id, from there you can call functions on this text through many small functions. Your [SDK](getting-started.md#choosing-an-sdk) should implement this in an OOP way that allows the user to store and manipulate text objects easily on the extension while forwarding all changes to Moss.

### Functions for managing text

```python
moss_text_make(text: str, font: str, font_size: int, colors: TextColors) -> ConfigGet[int]
```

Creates a text and gives you the ID that you can use to refer to this text object. Please note that the font here refers to the font path.

Any further functions where you see `text_id: int` it is referring you to pass the ID you got from `moss_text_make` .

```python
moss_text_set_text(text_id: int, text: str) -> Rect
```

This updates the text object and renders new text, this operation shouldn't be done extensively unless your text needs to change often, text objects are optimized to not be updated often and just displayed.

```python
moss_text_set_font(text_id: int, font: str, font_size: int) -> Rect
```

This updates both the font file, given a path and the font size, it will also regenerate the text object for you and position it in the center of wherever it was before.

{% hint style="info" %}
Notice that the above functions return the text rect, this is important and it is due to the fact that the rect of the text would have changed. It simplifies calls
{% endhint %}

```python
moss_text_set_rect(text_id: int, rect: Rect)
```

Updates the text rect, this determines the text position.

```python
moss_text_get_rect(text_id: int) -> Rect
```

Gets the text rect, the reason it's a rect is to provide the text size. The [SDK](getting-started.md#choosing-an-sdk) you use should probably run this after making a text in order to have all the values of the text locally in your extension

### Displaying text

```python
moss_text_display(text_id: int)
```

There's not much special about this function, it will display the text at the topleft of the rect, the size of the rect is determined by the text size so the text should be effectively be drawn within this are. Please note that the text background you passed is automatically drawn too as part of this operation.

## Basic API usage

### API Models

```
RM_File:
- content_count: int - The amount of sub data included in the file
- hash: str - The file hash
- rm_filename: str - A reference to the rm_filename Header for this file
- size: int - The total byte size of all sub data(s) / data combined
- uuid: str - The uuid of the file (This can include the file extension typically)
```

```
RM_TimestampedValue[T]:
- timestamp: str - A string formatted datetime
- value: Optional[T] - The stored typed value
```

```
RM_Tag:
- name: str - The name of the tag
- timestamp: int - The last time it was added
```

```
RM_Page:
- id: str
- index: RM_TimestampedValue
- template: RM_TimestampedValue
- redirect: Optional[RM_TimestampedValue]
- scroll_time: Optional[RM_TimestampedValue]
- vertical_scroll: Optional[RM_TimestampedValue]
```

```
RM_CPagesUUID:
- first: str - Author uuid
- second: int - Index?
```

```
RM_CPages:
- pages: List[RM_Page]
- original: RM_TimestampedValue
- last_opened: RM_TimestampedValue
- uuids: List[RM_CPagesUUID] - The uuids of the authors
```

```
RM_Zoom: # RAW
- zoomMode: ZoomModes
- customZoomCenterX: int
- customZoomCenterY: int
- customZoomPageHeight: int
- customZoomPageWidth: int
- customZoomScale: float
```

```
RM_Content:
- hash: str - The hash of the content file
- c_pages: RM_CPages - The full page information
- cover_page_number: int - Either 0 or -1, aka last page or first page
- file_type: FileTypes - The type of document, like notebook or epub...
- version: int - Should be 2, Moss will always convert version 1 to 2
- usable: bool - Used by moss to signify if it was able to fully parse the content
- zoom: RM_Zoom - The zoom preference on the document
- orientation: Orientations - The document's orientations
- tags: List[RM_Tag] - A list of the tags on the document
- size_in_bytes: int - The length in bytes of all the content data files combined
- dummy_document: bool - IDK ask reMarkable

- accessor: Accessor - Used to identify the location of the content
```

```
RM_Metadata:
- hash: str - The hash of the metadata file
- type: DocumentTypes - If it is a document or a collection
- parent: Optional[str] - if None then the parent is `My files` or "trash" otherwise uuid of collection
- created_time: int
- last_modified: int
- visible_name: str
- metadata_modified: bool
- modified: bool - IDK ask reMarkable
- synced: bool - IDK ask reMarkable
- version: Optional[int]

- accessor: Accessor - Used to identify the location of the metadata

# The metadata of documents includes this additional information
- last_opened: int - A timestamp of the last time the document was opened
- last_opened_page: int - The index of the last page opened
```

```
RM_DocumentCollection:
- tags: List[RM_Tag] - The list of tags on the collection
- metadata: RM_Metadata - The metadata for the collection
- uuid: str - The uuid of the collection, set parent to this to move a document
- has_items: bool - A variable provided by rmapi to indicate if it scanned any documents with this collection as the parent

- accessor: Accessor - Used to identify the location of the collection
```

```
RM_Document:
- files: List[RM_File] - All the files on this document
- content: RM_Content - The content information
- metadata: RM_Metadata - The document metadata
- uuid: str - The uuid of the document
- server_hash: Optional[str] - The hash of this file as it was last on the server (for checking changes)
- files_available: List[str] - A list of uuid(s) of the files that have been checked
- downloading: bool - If Moss has an operation to download data
- provision: bool - Used by Moss to signify if the document is staged for uploading
- available: bool - A property that shows if all the files are in the available files

- accessor: Accessor - Used to identify the location of the document
```

{% hint style="warning" %}
The above are made for connectivity of the extensions, some data is only used by Moss!Changing some things may not result in permanent changes, especially if the value is not a reMarkable value to begin with, or if you forgot to upload to the cloud!
{% endhint %}

Additionally here are some of the enums that you may have noticed above.

```
ZoomModes:
- 'bestFit' - Default
- 'customFit'
- 'fitToWidth'
- 'fitToHeight'
```

```
FileTypes:
- 'pdf'
- 'epub'
- 'notebook'
```

```
Orientations:
- 'portrait'
- 'landscape'
```

```
DocumentTypes:
- 'DocumentType'
- 'CollectionType'
```

### Accessors

Let's cover everything there is to know about how your extension manages document data inside of Moss. There are a few terms that will be used often and here's what they mean

* **API** item - The item is stored on **rm\_api** meaning that it will visible to menus and the api itself.
* **Standalone** item - The item is stored inside of the extension manager and not visible to **rm\_api** and won't show up in menus.
* **Sub** item - This can refer to a metadata/content inside of a document or collection. If this accessor is used, the uuid refers to the document or collection that the item is inside of.

{% hint style="warning" %}
Be careful since **rm\_api** is very particular about documents and will ensure only uploaded documents are in its list if synced.
{% endhint %}

#### The accessor data model

```
Accessor:
- type: str - The accessor item type
- uuid: Optional[str] - A potential uuid if the item exists
- id: Optional[int] - A potential id if the item exists
```

{% hint style="info" %}
It's important to note that some functions will not accept your accessor if they aren't made to handle it. For example you obviously cannot pass a metadata accessor to a document management function. It will throw a violation error.
{% endhint %}

{% hint style="warning" %}
The only models that use id for their accessor reference are the standalone metadata and content!
{% endhint %}

#### Accessors footnote

Moss has a way of dealing with the diverse quantity of data combinations. It uses what's called the accessor system, where each item access type is referenced by an accessor field.

{% hint style="success" %}
A note for SDK developers, your RM objects will receive their respective accessor reference. You do not need to worry much about the accessor, only making an updated copy in the case that you perform operations that change the identification of the object, such as **duplicate** or randomizing UUIDs!
{% endhint %}

#### The accessor list

The accessors are strings. You should check how your [SDK](getting-started.md#choosing-an-sdk) provides them if at all, these should otherwise be automatically handled by your [SDK](getting-started.md#choosing-an-sdk).

```
// Document API SUB
ACCESSOR_API_DOCUMENT_METADATA = "api_document_metadata"
ACCESSOR_API_DOCUMENT_CONTENT = "api_document_content"

// Collection API SUB
ACCESSOR_API_COLLECTION_METADATA = "api_collection_metadata"

// API
ACCESSOR_API_DOCUMENT = "api_document"
ACCESSOR_API_COLLECTION = "api_collection"

// Document Standalone SUB
ACCESSOR_STANDALONE_DOCUMENT_METADATA = "document_metadata"
ACCESSOR_STANDALONE_DOCUMENT_CONTENT = "document_content"

// Collection Standalone SUB
ACCESSOR_STANDALONE_COLLECTION_METADATA= "collection_metadata"

// Standalone
ACCESSOR_STANDALONE_DOCUMENT = "document"
ACCESSOR_STANDALONE_COLLECTION = "collection"

ACCESSOR_STANDALONE_METADATA = "metadata
ACCESSOR_STANDALONE_CONTENT= "content"

// Sync operations
ACCESSOR_FILE_SYNC_PROGRESS = "file_sync_progress"
ACCESSOR_DOCUMENT_SYNC_PROGRESS = document_sync_progress"

ACCESSOR_SYNC_STAGE = "sync_stage"

// Events - These do not contain physical objects
ACCESSOR_E_MOSS_FATAL = "moss_fatal"
ACCESSOR_E_API_FATAL = "api_fatal"
```

### Data models

These models are referenced below when creating new instance of API objects

{% hint style="warning" %}
You can either pass the data as bytes or file paths which are more efficient. Both of these values are otherwise optional, but Moss will complain if you didn't pass one!
{% endhint %}

```
DocumentNewNotebook:
- name: str - This is the visible name
- parent: Optional[str] - Null is `My Files` and so on...
- accessor: Accessor - You can leave uuid blank to get a random one by Moss
- page_count: int - Just pass 1 for default

- notebook_data: Optional[List[bytes]] - A list of raw .rm file bytes
or
- notebook_files: Optional[List[str]] - A list of paths to .rm files

- metadata_id: Optional[str]
- content_id: Optional[str]
```

```
DocumentNewPDF:
- name: str

- pdf_data: Optional[bytes] - The raw PDF bytes
or
- pdf_file: Optional[str] - The path to the PDF

- parent: Optional[str]
- accessor: Accessor - You can leave uuid blank to get a random one by Moss
```

```
DocumentNewEPUB:
- name: str

- epub_data: Optional[bytes] - The raw EPUB bytes
or
- epub_file: Optional[str] - The path to the EPUB

- parent: Optional[str]
- accessor: Accessor - You can leave uuid blank to get a random one by Moss
```

```
MetadataNew:
- name: str - Referring to the visible name
- parent: Optional[str] - The UUID of the parent collection or None so on...
- document_type: Optional[DocumentTypes] - The type of metadata to create
```

{% hint style="success" %}
Not passing a document\_uuid will use a randomly generated uuid which you'll receive from the function. See below.
{% endhint %}

### Main accessor functions

```python
moss_api_get(accessor: Accessor, key: str) -> ConfigGet[T]
```

This function gets only one field from the accessor.

```
_moss_api_set(accessor: Accessor, value: ConfigSet[T])
```

This function sets only one field of the accessor.

```python
moss_api_get_all(accessor: Accessor) -> ConfigGet[T]
```

This function will fetch the entire accessor with all it's fields.

### Functions for documents

All the functions here are related to either creating or managing documents

#### Creating documents

{% hint style="info" %}
Each creating function below returns the new document's UUID. Your [SDK](getting-started.md#choosing-an-sdk) should apply it to the accessor automatically.
{% endhint %}

{% hint style="warning" %}
Refer to your [SDK](getting-started.md#choosing-an-sdk) for specific implementations. Typically since most fields are not required, the SDK should use a builder with defaults for the fields that aren't needed.
{% endhint %}

```python
moss_api_document_new_notebook(value: DocumentNewNotebook) -> str
moss_api_document_new_pdf(value: DocumentNewPDF) -> str
moss_api_document_new_epub(value: DocumentNewEPUB) -> str
```

#### Managing documents

```python
moss_api_document_duplicate(accessor: Accessor) -> str
```

Returns the UUID of the new duplicate. This function randomizes a lot of the UUIDs of the document, it will also update timestamps and set the document to provision.

```python
moss_api_document_randomize_uuids(accessor: Accessor) -> str
```

This function is self explanatory, it will modify all the document UUIDs including nested UUID references to a new random UUID and return the new UUID.

```python
moss_api_document_unload_files(accessor: Accessor)
```

Simply unloads any files that Moss has loaded on the document. Documents will usually be automatically unloaded upon closing. If your extension loaded files though, this is the way to unload them and you should!

```python
moss_api_document_load_files_from_cache(accessor: Accessor)
```

This function loads all the files enforcing cache usage only. If the cache misses a file, it will not be downloaded.

```python
moss_api_document_ensure_download_and_callback(accessor: Accessor, callback: str)
```

Document downloads are threaded, this is one way to check for when your document has finished downloading. The callback as all other extension functions accepts the name of your extension callback function.

```python
moss_api_document_ensure_download(accessor: Accessor)
```

This function is very similar to the above, but it does not run a callback. It will halt until the document is finished downloading.

{% hint style="success" %}
The above download functions will also load the data, including using cache!
{% endhint %}

```python
moss_api_document_export(accessor: Accessor)
```

This function prepares the document for uploading to the cloud. It prepares data and hashes converting the metadata and content data into raw data for upload.

{% hint style="warning" %}
This function does not upload the document to the cloud. Nor should you need to use it unless you are doing some form of manual upload processing. This function is internally automatically used by Moss before the upload happens, as the raw document data needs to be ready before upload, this means you can't modify anything during this process if you use the automatic **rm\_api** upload functionality.
{% endhint %}

### Functions for metadata

```python
moss_api_metadata_new(value: MetadataNew) -> int
```

Creates a new standalone metadata object and returns the id of it.

### Functions for content

```python
moss_api_content_new_notebook(page_count: int) -> int
```

This function creates a content object for a blank notebook with a specified page count. You must pass at minimum one page! Returns standalone content id

```python
moss_api_content_new_pdf() -> int
moss_api_content_new_epub() -> int
```

These functions create blank content objects for pdf and epub. Notice that they do not identify any data, it's just a blank content template, the data for the pdf or epub would be on the document object. If you wanted to make a pdf or epub document check the document creation functions above. Returns standalone content id.

## Advance API usage

This covers _**real**_ API interactions. So be careful what you do. Always test on a suitable secondary account if possible, and use the recovery tools provided by the open source version of Moss if you ever find yourself in a pickle.

You'll notice that accessors are used here too. Extension manager will catch any loose sync progress objects and make them available to your extension. So you can receive external sync operations as well as start your own.

### Advance API models

```
API_FileSyncProgress:
- done: int - The amount of operations completed
- total: int - The total amount of operations, this is dynamic
- stage: Optional[str] - An optional stage, used by the menu to change indicator icon
- finished: bool - Indicates that the sync operation is fully completed

- accessor: Accessor - Uses ID, check above for the accessor types
```

```
API_DocumentSyncProgress(API_FileSyncProgress): - Adds extra fields onto sync progress
- document_uuid: str - Indicates which document the operation is for, used by menus
- file_sync_operation: RM_FileSyncProgress - Indicates a progress of all files
- total_tasks: int - Indicates the amount of files to upload
- finished_tasks: int - Indicates the amount of files uploaded
- _tasks_was_set_once: bool - This internally used to indicate that the sync began

- accessor: Accessor - Uses ID, check above for the accessor types
```

```
RM_RootInfo:
- generation: int - A number for reference (IDK ask reMarkable)
- hash: str - The hash of the file that is root / to be root
```

```
RM_FileList:
- version: int - It is usually 3 don't worry about it much
- files: List[RM_File] - A list of content files or docfiles if it is the root
```

### Making sync operations

Some API functions require you to define a sync operation before you call them. These are simple objects for tracking progress. Moss provides two functions for creating both sync operation types

```python
moss_api_new_file_sync_progress() -> int
```

In Moss a file sync operation contains all the tasks to be completed for this sync task. This returns the operation ID.

```python
moss_api_new_document_sync_progress(
    file_sync_progress: Accessor, document_uuid: str,
)
```

Document sync operations are more specific since they internally need a file sync operation too. They identify the document and have the top most amount of steps/files needed to upload the document. If this is sent to the menus it will display as a progress bar of the files being uploaded. The file sync progress on the other hand is usually contains the total amount of bytes.

{% hint style="info" %}
Please note that these operations need to be transmitted as events in the API for them to register in menus. API functions requesting sync progress object will usually do this for you. However you can also send events for these yourself if you has some custom sync event going on.
{% endhint %}

### Creating your own sync messages and icons

Moss has an accessor for this but there are a few things to note.

First off ALL stages of sync from 0 until 99 are reserved by **rm\_api** so you cannot set new ones under those indexes, but if you desire you can modify them.

You can check what sync stages **rm\_api** has [here](https://github.com/RedTTGMoss/rm_api/blob/main/sync_stages.py). These are unlikely to change.\
Your extension can create its own stage between 100 - 999.

What you want to do is simply use the accessor `sync_stage` (id is the index) and set the individual icon and text using `moss_api_set`

#### The result

<figure><img src="../.gitbook/assets/custom_sync_stage.png" alt=""><figcaption><p>Rust SDK custom sync stage</p></figcaption></figure>

### Raw API requests _<mark style="color:red;">BE CAREFUL!!!</mark>_

These functions allow you to access the user cloud directly. The protective measures of Moss and **rm\_api** won't be there, so be very careful what you are doing and make sure to ask for user consent. Be careful how you test your extension, always use a test cloud for these kinds of things. Follow reMarkable's cloud conventions to protect the user from take down.

```python
moss_api_get_root() -> RM_RootInfo
```

This function will fetch the current root file from the cloud. Please note that if the generation is missing Moss is running in a semi-offline mode. You won't be able to perform any further actions except maybe getting cached files. Moss keeps track of the last synced root file and if it is offline this is what you will get, but without the generation.

```python
moss_api_get_file(file_hash: str, use_cache: bool) -> RM_FileList
```

This function is mainly for getting the list of files in one of the `.doc` entries, this includes the root file and all of the file it lists, after that they contain actual data files `root->docfile->*content`

```python
moss_api_get_file_contents(...) -> ...
```



```python
moss_api_put_file(...)
```



```python
moss_api_get_file_contents(...) -> ...
```



```python
moss_api_check_file_exists(...) -> bool
```



```python
moss_api_update_root(...)
```

Tells the cloud the file that should become your new root file. <mark style="color:red;">**Ensure it is uploaded!!!**</mark>

### Miscellaneous functions

```python
moss_api_spread_event(accessor: Accessor)
```

This function will spread an event to any event subscriber on the **rm\_api**. These include the sync operation events but also other events which Moss can spread for you, check [accessors](host-functions.md#accessors) above.
