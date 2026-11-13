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
