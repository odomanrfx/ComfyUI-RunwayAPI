from comfy_api.input_impl import VideoFromFile
import requests
import base64
from PIL import Image
import tempfile
import os
import io
import time
import torchvision.io as tvio
import pathlib

"""
IN TESTING VERSION
"""

MAX_BYTES = 16 * 1024 * 1024  # 16 MB
DATA_URI_THRESHOLD = 3_200_000

API_URL = "https://api.dev.runwayml.com"

def image_to_data_uri(image_tensor, format="PNG"):
    """Convert ComfyUI IMAGE tensor to a base64 data URI (PNG by default)."""

    # pull out a NumPy array
    arr = image_tensor.mul(255).byte().cpu().numpy()
    print(f"[image_to_data_uri] raw shape: {arr.shape}")

    # squeeze out singleton batch if needed
    if arr.ndim == 4 and arr.shape[0] == 1:
        arr = arr[0]
        print(f"[image_to_data_uri] squeezed batch → new shape: {arr.shape}")

    # handle the different 2D/3D layouts
    # C×H×W  → H×W×C
    if arr.ndim == 3 and arr.shape[0] in (1, 3):
        arr = arr.transpose(1, 2, 0)
        print(f"[image_to_data_uri] transposed C×H×W → H×W×C: {arr.shape}")

    # H×W×C 
    elif arr.ndim == 3 and arr.shape[2] in (1, 3):
        print(f"[image_to_data_uri] already H×W×C: {arr.shape}")

    # H×W grayscale
    elif arr.ndim == 2:
        print(f"[image_to_data_uri] grayscale H×W: {arr.shape}")

    else:
        raise ValueError(f"Unexpected image shape after squeeze: {arr.shape}")

    # convert to PIL and then to bytes
    pil = Image.fromarray(arr)
    buf = io.BytesIO()
    pil.save(buf, format=format)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    uri = f"data:image/{format.lower()};base64,{b64}"
    #print(f"[image_to_data_uri] returning URI length={len(uri)}")

    return uri

def video_to_data_uri(video_obj, fps=24, codec="h264"):
    """Encode a VIDEO (VideoFromFile or tensor) to MP4 and return a base64 data URI."""

    # Case 1: VideoFromFile wrapper
    if isinstance(video_obj, VideoFromFile):
        try:
            # try in-memory stream first
            stream = video_obj.get_stream_source()
            data = stream.read()
        except Exception:
            # fallback: write out to a temp MP4
            tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            video_obj.save_to(tmp.name)
            with open(tmp.name, "rb") as f:
                data = f.read()

    # Case 2: Tensor from VideoDecoder upstream
    elif hasattr(video_obj, "cpu"):
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tvio.write_video(tmp.name, video_obj.cpu(), fps=fps, video_codec=codec)
        with open(tmp.name, "rb") as f:
            data = f.read()

    else:
        raise ValueError(f"Unsupported video type: {type(video_obj)}")

    # Convert to base 64
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:video/mp4;base64,{b64}"

def video_obj_to_path(video):
    """ Resolve a ComfyUI VIDEO to a real .mp4 path (existing path, save_to, or stream)."""
    # If path is already a string
    if isinstance(video, str) and os.path.isfile(video):
        return video

    #  Some wrappers expose a direct attribute with the path (name varies)
    for attr in ("file_path", "filepath", "filename"):
        p = getattr(video, attr, None)
        if isinstance(p, str) and os.path.isfile(p):
            return p

    # Preferred: have object to write itself to disk
    if hasattr(video, "save_to"):
        fd, tmp = tempfile.mkstemp(suffix=".mp4"); os.close(fd)
        video.save_to(tmp)
        return tmp

    # Fallback: read a stream and write it yourself
    if hasattr(video, "get_stream_source"):
        stream = video.get_stream_source()
        fd, tmp = tempfile.mkstemp(suffix=".mp4"); os.close(fd)
        with open(tmp, "wb") as f:
            f.write(stream.read())
        return tmp

    raise TypeError(f"Unsupported VIDEO object type: {type(video)}; available attrs: {dir(video)}")
    # Case 1: VideoFromFile wrapper 
    if isinstance(video_obj, VideoFromFile):
        try:
            # try in-memory stream first
            stream = video_obj.get_stream_source()
            data = stream.read()
        except Exception:
            # fallback: write out to a temp MP4
            tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            video_obj.save_to(tmp.name)
            with open(tmp.name, "rb") as f:
                data = f.read()

    # Case 2: Tensor from VideoDecoder upstream 
    elif hasattr(video_obj, "cpu"):
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tvio.write_video(tmp.name, video_obj.cpu(), fps=fps, video_codec=codec)
        with open(tmp.name, "rb") as f:
            data = f.read()

    else:
        raise ValueError(f"Unsupported video type: {type(video_obj)}")

    # Convert to base 64
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:video/mp4;base64,{b64}"

def upload_video_catbox_mp4(path):
    """Upload an MP4 (≤16 MB) to catbox.moe and return the public URL."""

    p = pathlib.Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    if p.stat().st_size > MAX_BYTES:
        mb = p.stat().st_size / (1024 * 1024)
        raise ValueError(f"Video is {mb:.2f} MB — exceeds 16 MB limit.")

    with p.open("rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (p.name, f, "video/mp4")},
            timeout=180,
        )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"Unexpected Catbox response: {r.text[:200]}")
    return url

def wait_for_task(task_id: str, headers: dict, poll_interval: float = 1.0, max_wait: float = 300.0):
    """
    Polls /v1/tasks/{task_id} until it reaches a terminal state (SUCCEEDED or FAILED).
    Handles PENDING, THROTTLED, RUNNING by sleeping and retrying.
    """
    url = f"{API_URL}/v1/tasks/{task_id}"
    elapsed = 0.0

    while elapsed < max_wait:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        status = r.json().get("status", "").upper()

        if status == "PENDING":
            # job has been received, but no work started yet
            print("Pending…")
        elif status == "THROTTLED":
            # you’re being rate-limited; back off a bit longer
            print("Throttled, backing off…")
            time.sleep(poll_interval * 2)
            elapsed += poll_interval * 2
            continue
        elif status == "RUNNING":
            # work is in progress
            print("Running…")
        elif status == "SUCCEEDED":
            # finished successfully
            print("Succeeded!")
            return r.json()  # contains your output URLs / data
        elif status == "FAILED":
            # something went wrong
            raise RuntimeError(f"Task failed: {r.json().get('error', 'no error message')}")
        else:
            # unexpected status
            print(f"Unknown status `{status}`; retrying…")

        # sleep before next poll
        time.sleep(poll_interval)
        elapsed += poll_interval

    # timed out
    raise TimeoutError(f"Task {task_id} did not finish after {max_wait}s")

class RunwayAPI_Client:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                    },
                )
            },
        }

    RETURN_TYPES = ("RUNWAYCLIENT",)
    RETURN_NAMES = ("api_key",)
    FUNCTION = "run"
    CATEGORY = "RodeoFX/Runway"
   

    def run(self, api_key):
        """
        Create a Runway client with the provided API key.
        """

        if api_key == "":
            raise ValueError("API Key is required")

        api_key = {"auth_token": api_key}

        return (api_key,)
    
class RunwayAPI_Aleph:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("RUNWAYCLIENT", {"forceInput": True}),
                "video": ("VIDEO", {"forceInput": True}), 
                "reference_image": ("IMAGE", {"forceInput": True}),
                "prompt" : ("STRING", {"multiline": True, "default": ""}, ),
                "ratio": (["1280:720","720:1280", "1104:832", "960:960", 
                           "832:1104", "1584:672", "848:480", "640:480"], {"default": "1280:720"}),
            },
            "optional": {
                "seed": ("INT", {"default": 0}),
                "publicFigureThreshold":  (["auto", "low"], {"default": "auto"}),
            },
        }
    
    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("jpg urls", )
    FUNCTION = "run"
    CATEGORY = "RodeoFX/Runway"

    def run(self, api_key, video, reference_image, prompt, ratio, seed, publicFigureThreshold):
        key = api_key['auth_token']
        print(f"Key received: {key}")

        headers = {
            "Content-Type":     "application/json",
            "Authorization":    f"Bearer {key}",
            "X-Runway-Version": "2024-11-06",
        }

        # Convert video to file path and upload using improved method
        print("[RUNWAY API] Processing video...")
        video_path = video_obj_to_path(video)
        print(f"[RUNWAY API] Video path: {video_path}")

        # Choose method based on size of video
        size = os.path.getsize(video_path)
        if size <= DATA_URI_THRESHOLD:
            video_url = video_to_data_uri(video_path)
        else:
            video_url = upload_video_catbox_mp4(video_path)

        # Convert reference image to a uri
        referenceUri = image_to_data_uri(reference_image)

        payload = {
            "videoUri":         video_url,
            "promptText":       prompt,
            "seed":             seed,
            "model":            "gen4_aleph",
            "ratio":            ratio,
            "references": [ {"type":"image", "uri": referenceUri} ],
            "contentModeration": {"publicFigureThreshold": publicFigureThreshold}
        }

        print(f"[RUNWAY API] Sending payload to Runway...")
        print(f"[RUNWAY API] Video URL type: {'Base64 Data URI' if video_url.startswith('data:') else 'External URL'}")
        print(f"[RUNWAY API] Prompt: {prompt}")
            
        response = requests.post(f"{API_URL}/v1/video_to_video", json=payload, headers=headers)

        # Error handling for debugging
        if not response.ok:
            print(f"[RUNWAY API ERROR] Status Code: {response.status_code}")
            try:
                error_json = response.json()
                print(f"[RUNWAY API ERROR] Error Details: {error_json}")
            except:
                print(f"[RUNWAY API ERROR] Raw Response: {response.text}")

        response.raise_for_status()
        result = response.json()

        id = result.get("id")
        print(f"[RUNWAY API] Task created with ID: {id}")

        task_headers = {
            "Authorization":    f"Bearer {key}",
            "X-Runway-Version": "2024-11-06",
        }

        final = wait_for_task(id, task_headers)  
        
        print(f"[RUNWAY API] Task completed successfully")

        urls = final.get('output')
        video_url = urls[0]

        print(f"[RUNWAY API] Output URL: {video_url}")

        return(video_url, )