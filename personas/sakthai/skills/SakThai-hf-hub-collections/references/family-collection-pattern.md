# Family Collection Pattern

Create a themed collection bundling all models + datasets from the same project family.

## When to use

After publishing multiple related models (e.g. a base model + adapters + GGUF variants + embedding models). A family collection makes them discoverable as a unified project.

## Steps

### 1. Create collection

```python
col = create_collection(
    title='SakThai Model Family',
    description='All SakThai models and datasets — tool-calling LLMs, embeddings, code, vision, TTS.'
)
```

### 2. Add models, datasets, and Spaces

```python
items = [
    ('Nanthasit/sakthai-context-1.5b-merged', 'model'),
    ('Nanthasit/sakthai-embedding', 'model'),
    ('Nanthasit/sakthai-combined-v6', 'dataset'),
    ('Nanthasit/sakthai-tts', 'space'),
]
for item_id, item_type in items:
    add_collection_item(col.slug, item_id, item_type=item_type, exists_ok=True)
```

### 3. Add descriptive notes to top items

```python
col = get_collection(col.slug)
for item in col.items:
    if '1.5b' in item.item_id and not item.note:
        add_collection_item(col.slug, item.item_id, item_type='model',
            note='🏆 Most popular — 942 downloads, 4/5 BFCL tool-calling',
            exists_ok=True)
```

### 4. Cross-link from every model card

Add to each model's README.md:

```markdown
## SakThai Model Family

| Model | Size | Type | Downloads |
|-------|:----:|:----:|:---------:|
| [1.5B-merged](...) | 934 MB | Tool-calling | 942 |

[Full collection →](https://huggingface.co/collections/...)
```

## Example result

Collection: `Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02`

Items: 12 models + 2 datasets + Spaces. Each model card links back to the family table.

## Pitfalls

- **Collection slug contains a hash**: Save the slug after creation. It can't be changed.
- **`exists_ok=True` is critical**: Without it, adding an already-present item returns HTTP 409.
- **Item types are lowercase**: `"model"`, not `"Model"` or `"models"`.
- **Notes have 500-char limit**: Longer notes are silently truncated.
