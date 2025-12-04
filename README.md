# ComfyUI Text Templates

Compose text by injecting wired text inputs into an editable template. Useful for chaining LLM outputs and building context.

## Installation

### ComfyUI Manager
Search for "Text Templates" in ComfyUI Manager and click Install.

### Manual
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/redrockvp/comfyui-text-templates.git
```
Restart ComfyUI.

## Usage

1. Add the **Text Template** node (category: `text`)
2. Write your template using `{1}`, `{2}`, etc. as placeholders
3. Connect text outputs from other nodes to `text_1`, `text_2`, etc.
4. Unconnected placeholders remain as-is in the output

### Example

**Template:**
```
You are a {1}. The user says: {2}
```

**Inputs:**
- `text_1`: "helpful assistant"
- `text_2`: "Hello!"

**Output:**
```
You are a helpful assistant. The user says: Hello!
```

## Node Reference

| Input | Type | Description |
|-------|------|-------------|
| template | STRING | Multiline text with `{1}`-`{6}` placeholders |
| text_1 - text_6 | STRING | Optional wired inputs from upstream nodes |

| Output | Type | Description |
|--------|------|-------------|
| text | STRING | Resolved template with substitutions |

## License

MIT
