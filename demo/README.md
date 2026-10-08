---
title: DisSModel Cellular Automata Explorer
emoji: 🗺️
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
license: mit
short_description: Run the dissmodel-ca cellular automata in the browser
---

# Cellular Automata Explorer

Interactive demo of [dissmodel-ca](https://github.com/DisSModel/dissmodel-ca):
pick a model, set its parameters in the sidebar and run it on a vector grid.

This folder is self-contained and is what gets deployed:

```bash
# locally
pip install -r requirements.txt
streamlit run app.py

# or with Docker
docker build -t ca-demo . && docker run -p 7860:7860 ca-demo
```

To publish on Hugging Face, create a Space with the Docker SDK and push the
contents of this folder to it. The header above is the Space configuration.
