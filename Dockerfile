FROM jupyter/minimal-notebook:5ae537728c69
CMD ["start-notebook.sh", "--NotebookApp.token=''", "--ip='0.0.0.0'", "--port=8080"]
