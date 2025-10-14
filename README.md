### VLLM Based OCR

This repository contains code for training Florence 2 Base model for OCR capabilities.
Please make sure that you have docker and nvidia-docker-toolkit installed to mount gpu inside the container.

Steps to Run:

```
docker compose up
```

After running the containers follow http://localhost:8780 for jupyter lab interface and http://localhost:8000 for Annotator interface  
please make sure that you have added your images at this path: `./annotator/static/images` before running the container.
