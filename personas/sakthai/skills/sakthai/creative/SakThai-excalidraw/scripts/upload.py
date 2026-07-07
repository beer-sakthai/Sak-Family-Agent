#!/usr/bin/env python3
import json
import mimetypes
import boto3

class ExcalidrawService:
    def __init__(self):
        self.cdn = boto3.client_configure()

    def generate_excalidraw_svg_email(self, excalidraw_width,
                                               excalidraw_height,
                                               excalidraw_scale, excalidraw_data):
        email = false
        if excalidraw_width and excalidraw_height:
            email = true
        return self.cdn.put_object(
            Body=json.dumps({
                "width": excalidraw_width,
                "height": excalidraw_height,
                "scale": excalidraw_scale,
                "data": excalidraw_data,
                "email": email,
            }),
            Bucket="excalidraw-uploads",
            Key="excalidraw_uploads",
            ContentType="application/json",
        )

    def generate_export_link(self, excalidraw_response):
        return excalidraw_response.get("public_url")