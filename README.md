# Machine Learning Python Function

This repo contains a Machine Learning Python Function that can be deployed as a TAP workload.

The function is used to determining the age of Abalones. This project leverages a dataset located on a Greenplum database and utilizes the Greenplum Python library to boost the machine learning algorithm.

This function utilizes the buildpacks provided by VMware's open-source [Function Buildpacks for Knative](https://github.com/vmware-tanzu/function-buildpacks-for-knative) project.

## Getting Started

To begin editing your function, refer to the tree diagram below of the file to modify:

```
python-function
    └── func.py // EDIT THIS FILE
```

Inside this file, you will find a function that is invoked by default. For example:

```
def main(data: Any, attributes: dict):
    # Your function implementation goes here
    return attributes, "Hello world!"
```

You may replace the code inside this default function with your logic.

To see samples of code deployable as a Function (FaaS) experience, visit the [samples folder](https://github.com/vmware-tanzu/function-buildpacks-for-knative/tree/main/samples/python).

## Tanzu Application Platform Accelerator

To add the accelerator in Tanzu Application Platform

~~~
tanzu acc create greenplum-python --git-repo https://github.com/fklein82/python-function --git-branch main --interval 5s\n
~~~

## Deploying

Please see [DEPLOYING.md](DEPLOYING.md) on how to build, deploy, and test your newly built function.

### Deploying to Kubernetes as a TAP workload with Tanzu CLI

You need to select `Include TAP deployment resources` when generating the project for the steps below to work.

When you are done developing your function, you can simply deploy it using:

```
tanzu apps workload apply -f config/workload.yaml
```

If you would like deploy the code from your local working directory you can use the following command:

```
tanzu apps workload create node-function -f config/workload.yaml \
  --local-path . \
  --source-image <REPOSITORY-PREFIX>/node-function-source \
  --type web
```

### Interacting with Tanzu Application Platform

Determine the URL to use for the accessing the app by running:

```
tanzu apps workload get python-function
```

> NOTE: This depends on the TAP installation having DNS configured for the Knative ingress.

After deploying your function, you can interact with the function by using:

> NOTE: Replace the <URL> placeholder with the actual URL.


# JupyterLab

### Add Jupyter Nodebook with TAP (example)

~~~
tanzu apps workload create jupyter \
  --git-repo https://github.com/fklein82/python-function \
  --git-branch main \
  --param dockerfile=./Dockerfile \
  --label apps.tanzu.vmware.com/has-tests=true \
  --type web
~~~

## Build the docker image for jupyter:
~~~
docker build . --file Dockerfile --tag jupyter-for-tap:1.0

docker tag jupyter-for-tap:1.0 registry.fklein.me/mlops/jupyter-for-tap:1.0

docker login registry.fklein.me

docker push registry.fklein.me/mlops/jupyter-for-tap:1.0
~~~

## Deploy Jupyter as web service on tap
Finally, deploy to TAP:

~~~
tanzu apps workload create jupyter-nodebook-v2 \
  --type web \
  --label app.kubernetes.io/part-of=jupyter-app \
  --annotation autoscaling.knative.dev/min-scale=1 \
  --image registry.fklein.me/mlops/jupyter:2023-07-05-16-26-29
~~~

