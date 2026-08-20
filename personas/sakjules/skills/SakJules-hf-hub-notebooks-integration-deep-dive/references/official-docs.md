# Official HF Docs: Jupyter Notebooks on the Hugging Face Hub

Source: https://huggingface.co/docs/hub/en/notebooks
Fetched: 2026-07-30

---

[Jupyter notebooks](https://jupyter.org/) are a very popular format for sharing code and data analysis for machine learning and data science. They are interactive documents that can contain code, visualizations, and text.

## Open models in Google Colab and Kaggle

When you visit a model page on the Hugging Face Hub, you'll see a "Google Colab"/ "Kaggle" button in the "Use this model" drop down. Clicking this will generate a ready-to-run notebook with basic code to load and test the model. This is perfect for quick prototyping, inference testing, or fine-tuning experiments — all without leaving your browser.

Users can also access a ready-to-run notebook by appending /colab to the model card's URL. As an example, for Gemma 3 4B IT model:
- Model: https://huggingface.co/google/gemma-3-4b-it
- Colab: https://huggingface.co/google/gemma-3-4b-it/colab
- Kaggle: https://huggingface.co/google/gemma-3-4b-it/kaggle

If a model repository includes a file called `notebook.ipynb`, we will use it for Colab and Kaggle instead of the auto-generated notebook content. Model authors can provide tailored examples, detailed walkthroughs, or advanced use cases while still benefiting from one-click Colab integration. [NousResearch/Genstruct-7B](https://huggingface.co/NousResearch/Genstruct-7B) is one such example.

## Rendering .ipynb Jupyter notebooks on the Hub

Under the hood, Jupyter Notebook files (usually shared with a `.ipynb` extension) are JSON files. While viewing these files directly is possible, it's not a format intended to be read by humans. The Hub has rendering support for notebooks hosted on the Hub. This means that notebooks are displayed in a human-readable format.

Notebooks will be rendered when included in any type of repository on the Hub. This includes models, datasets, and Spaces.

### Launch in Google Colab

[Google Colab](https://colab.google/) is a free Jupyter Notebook environment that requires no setup and runs entirely in the cloud. It's a great way to run Jupyter Notebooks without having to install anything on your local machine.

All .ipynb files hosted on the Hub are automatically given a "Open in Colab" button. This allows you to open the notebook in Colab with a single click.

## Key Takeaways

- Model pages auto-generate Colab/Kaggle notebooks from metadata
- Custom `notebook.ipynb` overrides auto-generation
- `/colab` and `/kaggle` URL endpoints for direct access
- `.ipynb` files render natively on the Hub
- Every `.ipynb` has an "Open in Colab" button
- Notebooks work in all repo types: models, datasets, Spaces
