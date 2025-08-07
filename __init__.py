from .runway_nodes import (
    RunwayAPI_Client,
    RunwayAPI_Aleph,
)

NODE_CLASS_MAPPINGS = {
    "RunwayAPI_Client": RunwayAPI_Client,
    "RunwayAPI_Aleph": RunwayAPI_Aleph,
}

NODE_CLASS_NAME_MAPPING = {
    "RunwayAPI_Client": "Runway Client",
    "RunwayAPI_Aleph": "Runway Aleph",
}