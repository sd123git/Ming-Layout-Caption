Pro
17

Ming image edit - workflow enhancement
1

21

2



Updated: Nov 11, 2026

tool
ming-image
custom_node
Your first model is live

Downloads, generations, and positive reviews on it now count toward your Creator Score. Your first goal is Spark at 500, which unlocks: judge crucibles and hat Turf: your stickers count for your team (accounts made since Nov 1).

See your journey · Close


Remix
1000218662.png




Remix
1000217905.png


Download

Manage

2 variants available

Config Other

Best match
ming-image-edit_caption-node.json

17.14 KB


Verified: 4 days ago

Other Formats

Config

Best match
ming-image-edit_caption-node.json


Verified: 4 days ago

17.14 KB

Archive

ming_layout_caption.zip


Verified: 4 days ago

3.14 KB

This checkpoint includes a config file, download and place it along side the checkpoint.


Details
Edit
Type
Workflows
Stats
21
0
1
2
3
4
5
6
7
8
9
0
1
2
3
4
5
6
7
8
9

Reviews
Positive
(1)

Published
Nov 8, 2026

Base Model
Ming Image Design 0.1

Hash
AIR
civitai:
3042703
@
3458646
+
3360156
default creator card background decoration

2
0
1
2
3
4
5
6
7
8
9


1
0
1
2
3
4
5
6
7
8
9

sj4ai

Joined Mar 8, 2026

License:

MIT

Hide

He's an enhancement for the Ming Image 0.1 Design: Image Edit workflow, from:

https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_ming_image_01_design_image_edit.json

It's a custom node built to enhance the stock workflow. The zip contains a single file, on a Linux deploy: ComfyUI/custom_nodes/ming_layout_caption/__init__.py

The custom node in the zip is node 339 in the attached workflow.

MingLayoutCaption does the same job as the stock 339 subgraph, which was about 50 nodes. It produces the same caption from the same inputs, with zero diff against preview 250. The improvements:

One node replaces the regex and loop chain. It reads 91's boxes and 93's dict directly, so the data is no longer turned into strings and parsed back with regex.

No 12-box limit. The stock loop was hard-coded to 12 iterations, so extra boxes were dropped. The new node handles any number. Currently untested beyond 12, mileage may vary.

No junk layers. With fewer than 12 boxes, the stock loop added empty layers with zero coordinates to the caption. The new node only writes real boxes and skips zero-area ones.

Quotes and braces are safe. The stock regexes cut descriptions short at a " and broke on {}. The new node escapes text properly, so the caption is always valid JSON.

More input formats. It accepts the bbox format (0–1000), 91's pixel format (editor_state), or JSON strings, and it limits coordinates to the canvas.

Three override inputs:

boxes_json: the layout, in place of node 91.

ideogram_json: the style settings, in place of node 93.

caption_override: the full caption written by hand, sent as-is.

Lazy inputs. When an override is set, the upstream node it replaces isn't requested, and it doesn't run at all unless a preview node needs it.

Faster. Stock workflow ran in 42 seconds per pass. New node reduced it to 35 s on the first pass and 28 s on repeat passes wit new seed only.

Reusable logic. build_caption() is a plain Python function, so an upstream use case will build output that agrees with the graph.

Extra outputs. Besides the caption, it outputs the cleaned-up box list and a layer count.
