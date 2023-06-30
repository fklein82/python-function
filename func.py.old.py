import greenplumpython as gp
from typing import List

import dataclasses
import datetime


def main():
    db = gp.database("postgresql://gpadmin:changeme@35.225.47.84/warehouse")

    abalone = db.create_dataframe(table_name="abalone")
    import greenplumpython.builtins.functions as F

    abalone_train = db.create_dataframe(table_name="abalone_train")
    abalone_test = db.create_dataframe(table_name="abalone_test")


    @dataclasses.dataclass
    class LinregType:
        col_nm: List[str]
        coef: List[float]
        intercept: float
        serialized_linreg_model: bytes
        created_dt: str


    # -- Create function
    # -- Need to specify the return type -> API will create the corresponding type in Greenplum to return a row
    # -- Will add argument to change language extensions, currently plpython3u by default

    from sklearn.linear_model import LinearRegression
    import numpy as np
    import pickle

    @gp.create_column_function
    def linreg_func(length: List[float], shucked_weight: List[float], rings: List[int]) -> LinregType:
        X = np.array([length, shucked_weight]).T
        y = np.array([rings]).T

        # OLS linear regression with length, shucked_weight
        linreg_fit = LinearRegression().fit(X, y)
        linreg_coef = linreg_fit.coef_
        linreg_intercept = linreg_fit.intercept_

        # Serialization of the fitted model
        serialized_linreg_model = pickle.dumps(linreg_fit, protocol=3)

        return LinregType(
            col_nm=["length", "shucked_weight"],
            coef=linreg_coef[0],
            intercept=linreg_intercept[0],
            serialized_linreg_model=serialized_linreg_model,
            created_dt=str(datetime.datetime.now()),
        )


    linreg_fitted = (
        abalone_train.group_by("sex")
        .apply(lambda t: linreg_func(t["length"], t["shucked_weight"], t["rings"]), expand=True)
    )

    unnest = gp.function("unnest")
    array_append = gp.function("array_append")

    linreg_fitted.assign(
        col_nm2=lambda t: unnest(array_append(t["col_nm"], "intercept")),
        coef2=lambda t: unnest(array_append(t["coef"], t["intercept"])),
    )[["sex", "col_nm2", "coef2"]]


    @gp.create_function
    def linreg_pred_func(serialized_model: bytes, length: float, shucked_weight: float) -> float:
        # Deserialize the serialized model
        model = pickle.loads(serialized_model)
        features = [length, shucked_weight]
        # Predict the target variable
        y_pred = model.predict([features])
        return y_pred[0][0]


    linreg_test_fit = linreg_fitted.inner_join(
        abalone_test,
        cond=lambda t1, t2: t1["sex"] == t2["sex"],
        self_columns=["col_nm", "coef", "intercept", "serialized_linreg_model", "created_dt"]
    )

    linreg_pred = linreg_test_fit.assign(
        rings_pred=lambda t:
            linreg_pred_func(
                t["serialized_linreg_model"],
                t["length"],
                t["shucked_weight"],
            ),
    )[["id", "sex", "rings", "rings_pred"]]


    @dataclasses.dataclass
    class linreg_eval_type:
        mae: float
        mape: float
        mse: float
        r2_score: float


    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    @gp.create_column_function
    def linreg_eval(y_actual: List[float], y_pred: List[float]) -> linreg_eval_type:
        mae = mean_absolute_error(y_actual, y_pred)
        mse = mean_squared_error(y_actual, y_pred)
        r2_score_ = r2_score(y_actual, y_pred)

        y_pred_f = np.array(y_pred, dtype=float)
        mape = 100 * sum(abs(y_actual - y_pred_f) / y_actual) / len(y_actual)
        return linreg_eval_type(mae, mape, mse, r2_score_)


    print(linreg_pred.group_by("sex").apply(
        lambda t: linreg_eval(t["rings"], t["rings_pred"]), expand=True)
    )

