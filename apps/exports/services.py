import os
from .utils import ExportUtils
from .s3 import S3Service


class ExportService:
    @staticmethod
    def export_call_logs(data, format="csv"):
        headers = ["call_time", "phone_number", "duration", "call_type"]
        
        filename = f"export.{format}"
        file_path = f"/tmp/{filename}" # Check OS compatibility for path
        
        if format == "csv":
            content = ExportUtils.generate_csv(data, headers)
            # Write string content to file
            with open(filename, "w") as f:
                f.write(content)
        # Add other formats
        
        # Upload to S3
        url = S3Service.upload_file(filename)
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
            
        return url
