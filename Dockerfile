FROM jupyter/minimal-notebook:5ae537728c69
CMD ["start-notebook.sh", "--NotebookApp.token=''"]
