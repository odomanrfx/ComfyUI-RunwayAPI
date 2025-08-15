# ComfyUI-RunwayAPI

Custom ComfyUI nodes that call the [Runway API](https://docs.dev.runwayml.com/api/) —specifically the Gen-4 Aleph video_to_video endpoint with optional reference image(s). Use these to send a source video + prompt from ComfyUI, track the task, and return the finished output URL.

---
<p align="center">
  <img src="workflows/Runway_API_Aleph_Workflow.png" alt="Workflow Diagram" />
</p>

## Installation

### Installing manually

1. Navigate to the `ComfyUI/custom_nodes` directory.

2. Clone this repository:
   ```
   git clone https://github.com/odomanrfx/ComfyUI-RunwayAPI.git
   ```
   The local path should be `ComfyUI/custom_nodes/ComfyUI-Runway-API/*`, where `*` represents all the files in this repo.

 3. Install the Media Utilities by cloning this repository:
   ```
   git clone https://github.com/ThanaritKanjanametawatAU/ComfyUI-MediaUtilities
   ```
   The path should be `ComfyUI/custom_nodes/ComfyUI-MediaUtilities/*`, where `*` represents all the files in this repo.

## Nodes

### RunwayAPI_Client  
**Purpose:** Supply your Runway API key.  
- **Inputs:** _None_  
- **Parameters:**  
  - **API Key** (string) – enter it here or leave blank to load from `config.ini`.  
- **Outputs:**  
  - `api key` (string)
 
---

### RunwayAPI_Aleph (Video → Video) 
**Purpose:** Calls POST /v1/video_to_video on Runway’s Gen-4 Aleph.
- **Inputs:**  
  - `api_key` (RUNWAYCLIENT)
  - `video` (VIDEO) - source clip
  - `reference` (IMAGE)
- **Parameters (optional):**  
  - **prompt** (`string, multiline`)  
  - **seed** (int)  
  - **ratio** (enum): 1280:720, 720:1280, 1104:832, 960:960, 832:1104, 1584:672, 848:480, 640:480
  - **publicFigureThreshold** (enum): auto, low
- **Outputs:**  
  - `video url` string) – final output URL
 
**How it works (under the hood):**
- Small inputs (≤ ~3.2 MB): sent as data URI (data:video/mp4;base64,...) per Runway docs.
- Larger inputs: uploaded to a free host (e.g., Catbox) and the public URL is passed as videoUri.
- Polls /v1/tasks/{id} until status is SUCCEEDED and returns the output URL.

**Common 400s to check:**
- videoUri invalid/inaccessible (private link, expired URL, or oversized data URI).
- references image too large (data URI > ~3.3 MB after base64).
- Missing X-Runway-Version or wrong Authorization token.

---

## Workflows

Workflows will be provided in the `workflows/` directory and include:

- `.json` files you can import directly into ComfyUI
- Reference images showing the structure and flow of the nodes

---

## Notes

Workflows will be provided in the `workflows/` directory and include:

- **Data URI limits:** Runway accepts base64 data URIs where practical, but base64 inflates size ~33%. Keep raw assets ~≤ 3.2 MB to fit under ~5 MB data-URI guidance.
- **Free hosting:** For bigger clips, you need a public, direct-access URL. This repo uses a simple Catbox upload helper (≤ 16 MB). For larger files, switch to your company’s storage or another host with direct GET access.

---