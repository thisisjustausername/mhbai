from datatypes.result import Result


def clean_single_data(data: Result) -> Result:
    data._data = (
        data.data[0] if data.is_success is True and data.data is not None else None
    )
    return data
