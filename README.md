# ComfyUI-Higgsfield-API

This repository provides custom ComfyUI nodes that connect to the [Higgsfield API](https://www.higgsfield.ai/) for generating video from text or image prompts. It allows direct integration of Higgsfield's AI video generation into ComfyUI workflows with full control over prompt construction, image uploading, previewing, and saving.

---

## Installation

### Installing manually

1. Navigate to the `ComfyUI/custom_nodes` directory.

2. Clone this repository:
   ```
   git clone https://github.com/odomanrfx/ComfyUI-Higgsfield-API.git
   ```
   The path should be `ComfyUI/custom_nodes/ComfyUI-Higgsfield-API/*`, where `*` represents all the files in this repo.
  
3. Install the Media Utilities by cloning this repository:
   ```
   git clone https://github.com/ThanaritKanjanametawatAU/ComfyUI-MediaUtilities
   ```
   The path should be `ComfyUI/custom_nodes/ComfyUI-MediaUtilities/*`, where `*` represents all the files in this repo.

4. No further dependencies required to install, all included with the installation of ComfyUI. 

5. Start ComfyUI and enjoy using the Higgsfield API node!
 
---

## Features

- **Text-to-Video Generation**
  - **Input:** Prompt  
  - **Output:** Video URL → Downloaded Video  
  - Adjustable duration, aspect ratio, resolution, and seed

- **Image-to-Video Generation**
  - **Input:** Prompt + Image (hosted URL)  
  - **Output:** Video URL → Downloaded Video  
  - Option to use image as first or last frame

- **Integration with [MediaUtilities](https://github.com/ThanaritKanjanametawatAU/ComfyUI-MediaUtilities)**
  - Enables loading and saving video URLs as video files
  - Required for playback and local saving

- **Flexible Prompting**
  - Accepts typed prompts or upstream prompt generation nodes

- **ImgBB Support**
  - Auto-uploads images to ImgBB to obtain publicly accessible URLs for use with the Higgsfield API

---

## Workflows

Workflows are provided in the `workflows/` directory and include:

- `.json` files you can import directly into ComfyUI
- Reference images showing the structure and flow of the nodes

---

## Node Locations

- **Higgsfield Nodes:** `api node/video/Higgsfield`
- **ImgBB Nodes:** `image/upload`
- **Media Utilities Nodes:** `image/video/MediaUtilities`

---
