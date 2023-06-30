import greenplumpython as gp
from typing import List
from sklearn.linear_model import LinearRegression
import numpy as np
import pickle
import mlflow
import dataclasses
import datetime
import os



def main():
    db = gp.database("postgresql://gpadmin:changeme@35.225.47.84/warehouse")

    abalone = db.create_dataframe(table_name="abalone")
    import greenplumpython.builtins.functions as F

    abalone_train = db.create_dataframe(table_name="abalone_train")
    abalone_test = db.create_dataframe(table_name="abalone_test")

    print(abalone_test[:1])
    print(abalone_train[:1])
    @dataclasses.dataclass
    class LinregType:
        model_name: str
        col_nm: List[str]
        coef: List[float]
        intercept: float
        serialized_linreg_model: bytes
        created_dt: str
        run_id: str
        registered_model_name: str
        registered_model_version: str


    # -- Create function
    # -- Need to specify the return type -> API will create the corresponding type in Greenplum to return a row
    # -- Will add argument to change language extensions, currently plpython3u by default



    @gp.create_column_function
    def linreg_func(length: List[float], shucked_weight: List[float], rings: List[int]) -> LinregType:
        os.environ["AZURE_STORAGE_ACCESS_KEY"] = "t11uhpL2YqfeORTdQMKsKvoBBZBkiTLrccscNS5sKxmtBRKnE54b/lzDPAn9v8hAD8jHW5Gg9/wD+AStK6mU9A=="
        os.environ["AZURE_STORAGE_CONNECTION_STRING"] = "DefaultEndpointsProtocol=https;AccountName=mlflowdev01;AccountKey=t11uhpL2YqfeORTdQMKsKvoBBZBkiTLrccscNS5sKxmtBRKnE54b/lzDPAn9v8hAD8jHW5Gg9/wD+AStK6mU9A==;EndpointSuffix=core.windows.net"
        mlflow.set_tracking_uri("http://20.93.3.160:5000")
        mlflow.set_experiment('test')
        experiment = mlflow.get_experiment_by_name('test')
        experiment_id = experiment.experiment_id
        mlflow.autolog()
        with mlflow.start_run(experiment_id=experiment_id,nested=True) as run:
            model_name="model_greenplum"
            mlflow.log_param("start_run_test", "This is a test")
            X = np.array([length, shucked_weight]).T
            y = np.array([rings]).T

            # OLS linear regression with length, shucked_weight
            linreg_fit = LinearRegression().fit(X, y)
            linreg_coef = linreg_fit.coef_
            linreg_intercept = linreg_fit.intercept_
            mlflow.log_param("start_run_test2", "This is a test 2")
            # Serialization of the fitted model
            serialized_linreg_model = pickle.dumps(linreg_fit, protocol=3)
            mlflow.sklearn.log_model(linreg_fit, model_name)

            # Register the model to MLFlow
            model_uri = "runs:/{}/model".format(run.info.run_id)
            mv = mlflow.register_model(model_uri, model_name)
            mlflow.sklearn.log_model(
                    sk_model=linreg_fit,
                    artifact_path="model",
                    registered_model_name=model_name,
                )

            return LinregType(
                model_name=model_name,
                col_nm=["length", "shucked_weight"],
                coef=linreg_coef[0],
                intercept=linreg_intercept[0],
                serialized_linreg_model=serialized_linreg_model,
                created_dt=str(datetime.datetime.now()),
                run_id=str(run.info.run_id),
                registered_model_name=str(mv.name),
                registered_model_version=str(mv.version)
            )

    linreg_fitted = (
        abalone_train.group_by()
        .apply(lambda t: linreg_func(t["length"], t["shucked_weight"], t["rings"]), expand=True)
    )

    print(linreg_fitted[["model_name", "col_nm", "coef", "intercept", "created_dt", "run_id", "registered_model_name",
                   "registered_model_version"]])

    linreg_test_fit = linreg_fitted.cross_join(
        abalone_test,
        self_columns=["col_nm", "coef", "intercept", "serialized_linreg_model", "created_dt", "registered_model_name",
                      "registered_model_version"]
    )
    print(linreg_test_fit[:1])